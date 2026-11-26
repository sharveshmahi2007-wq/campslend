#!/usr/bin/env python3
"""
CampusLend / LendLoop - Python REST API Server & Connector
PSG iTech College Email OTP Authentication System
Enforces @psgitech.ac.in domain, Secure OTP generation & SHA-256 verification,
rate limiting, 5-minute expiry, max 5 attempts, and BCrypt-compatible password hashing.
"""

import sys
import os
import json
import time
import re
import base64
import hmac
import secrets
import hashlib
import smtplib
import ssl
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env file if present
ENV_PATH = os.path.join(STATIC_DIR, ".env")
if os.path.exists(ENV_PATH):
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
        print("[*] Loaded environment variables from .env")
    except Exception as e:
        print(f"[!] Warning reading .env: {e}")

COLLEGE_DOMAIN = "psgitech.ac.in"
OTP_EXPIRY_SECONDS = 300       # 5 minutes
OTP_MAX_ATTEMPTS = 5           # Max 5 failed attempts
OTP_COOLDOWN_SECONDS = 60      # 60s resend cooldown
VERIFICATION_TOKEN_TTL = 900   # Verification token valid for 15 minutes

# Demo seed accounts are disabled unless explicitly enabled AND a password is set.
SEED_DEMO_DATA = os.environ.get("SEED_DEMO_DATA", "false").lower() == "true"
DEMO_STUDENT_PASSWORD = os.environ.get("DEMO_STUDENT_PASSWORD", "").strip()

# ---- Security / hardening configuration ----
MAX_BODY_BYTES = int(os.environ.get("MAX_BODY_BYTES", 1_000_000))  # 1 MB request cap
AUTH_TOKEN_TTL_SECONDS = int(os.environ.get("AUTH_TOKEN_TTL_SECONDS", 86400))  # 24h
PBKDF2_ITERATIONS = 260_000

# Only these files may be served as static content. Everything else falls back
# to index.html; dotfiles such as .env and .git are never served.
STATIC_ALLOWLIST = {"index.html", "translations.js"}
STATIC_DIRS = {"assets"}
SECURITY_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' https: data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)

# HMAC signing secret for bearer tokens. Set AUTH_SECRET in production; if it is
# missing a random per-process secret is used (tokens are invalidated on restart).
AUTH_SECRET = os.environ.get("AUTH_SECRET", "").strip()
if not AUTH_SECRET:
    AUTH_SECRET = secrets.token_hex(32)
    print("[!] AUTH_SECRET is not set. Using an ephemeral secret; tokens will not "
          "survive a restart. Set AUTH_SECRET in .env for production.", flush=True)

# CORS: same-origin is always allowed. Extra origins must be explicitly listed.
ALLOWED_ORIGINS = {
    o.strip().rstrip("/")
    for o in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
}
ALLOW_FILE_ORIGIN = os.environ.get("ALLOW_FILE_ORIGIN", "false").lower() == "true"

# In-memory OTP storage
# email -> { "hash": str, "salt": str, "expires_at": float, "attempts": int, "last_sent": float, "verified": bool, "verification_token": str, "verified_at": float }
OTP_STORE = {}
OTP_LOCK = threading.RLock()

# Brute-force protection: key -> {"count": int, "first": float, "last": float}
LOGIN_ATTEMPTS = {}
OTP_REQUEST_ATTEMPTS = {}
RATE_LOCK = threading.Lock()
LOGIN_WINDOW_SECONDS = 900
LOGIN_MAX_ATTEMPTS = 10
OTP_IP_WINDOW_SECONDS = 3600
OTP_IP_MAX_REQUESTS = 20


def hash_password(password, salt=None):
    """PBKDF2-HMAC-SHA256 password hashing (salted, slow, constant-time verify)."""
    if not salt:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", str(password).encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password, stored_hash):
    """Verify a password against PBKDF2, BCrypt (Java backend), or legacy salted SHA-256.

    Plaintext comparison is intentionally NOT supported.
    """
    if not stored_hash:
        return False
    stored = str(stored_hash)

    # 1. PBKDF2-HMAC-SHA256 (current format)
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, expected = stored.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256", str(password).encode("utf-8"), salt.encode("utf-8"), int(iterations)
            )
            return hmac.compare_digest(digest.hex(), expected)
        except Exception:
            return False

    # 2. BCrypt hashes created by the Spring Boot backend
    if stored.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            import bcrypt  # optional dependency
            return bcrypt.checkpw(str(password).encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False

    # 3. Legacy salted SHA-256 (format: salt$hash) - upgraded on next login
    if "$" in stored:
        try:
            salt, expected = stored.split("$", 1)
            if not salt or not expected:
                return False
            digest = hashlib.sha256(f"{password}:{salt}".encode("utf-8")).hexdigest()
            return hmac.compare_digest(digest, expected)
        except Exception:
            return False

    return False


def password_needs_rehash(stored_hash):
    return not str(stored_hash or "").startswith("pbkdf2_sha256$")


# ---------------- Bearer token (HMAC-SHA256 signed) ----------------
def _b64url_encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_auth_token(student):
    now = int(time.time())
    payload = {
        "sub": str(student.get("studentId") or student.get("_id") or ""),
        "email": str(student.get("email") or "").lower(),
        "iat": now,
        "exp": now + AUTH_TOKEN_TTL_SECONDS,
        "nonce": secrets.token_hex(8),
    }
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(AUTH_SECRET.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64url_encode(signature)}"


def verify_auth_token(token):
    """Return the token payload when the signature and expiry are valid, else None."""
    try:
        body, signature = str(token).split(".", 1)
        expected = hmac.new(AUTH_SECRET.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, _b64url_encode(expected)):
            return None
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
        if not isinstance(payload, dict):
            return None
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        if not payload.get("sub"):
            return None
        return payload
    except Exception:
        return None


# ---------------- Rate limiting helpers ----------------
def _prune_rate_map(store, window, now):
    for key in [k for k, v in store.items() if now - v.get("first", 0) > window]:
        store.pop(key, None)


def rate_limit_allow(store, key, window, max_attempts):
    now = time.time()
    with RATE_LOCK:
        _prune_rate_map(store, window, now)
        rec = store.get(key)
        if rec and now - rec.get("first", 0) <= window:
            if rec.get("count", 0) >= max_attempts:
                return False
        else:
            store[key] = {"count": 0, "first": now}
    return True


def rate_limit_hit(store, key, window):
    now = time.time()
    with RATE_LOCK:
        rec = store.get(key)
        if not rec or now - rec.get("first", 0) > window:
            store[key] = {"count": 1, "first": now}
        else:
            rec["count"] = rec.get("count", 0) + 1


def rate_limit_clear(store, key):
    with RATE_LOCK:
        store.pop(key, None)


def purge_expired_otp_entries():
    now = time.time()
    with OTP_LOCK:
        for email in list(OTP_STORE.keys()):
            rec = OTP_STORE[email]
            if rec.get("verified"):
                if now > rec.get("verified_at", 0) + VERIFICATION_TOKEN_TTL:
                    OTP_STORE.pop(email, None)
            elif now > rec.get("expires_at", 0) + 3600:
                OTP_STORE.pop(email, None)


# ---------------- Input validation helpers ----------------
def clean_text(value, max_length=500, default=""):
    """Normalize untrusted text: strip control chars, trim, and cap length."""
    if value is None:
        return default
    text = str(value)
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    text = text.strip()
    if not text:
        return default
    return text[:max_length]


def safe_http_url(value, default=""):
    """Only allow absolute http(s) image URLs (blocks javascript:/data: markup injection)."""
    text = clean_text(value, max_length=2000)
    if not text:
        return default
    try:
        parsed = urllib.parse.urlparse(text)
        if parsed.scheme.lower() in ("http", "https") and parsed.netloc:
            return text
    except Exception:
        pass
    return default


def is_valid_phone(phone):
    """Validate phone string (6-30 allowed chars and at least 7 digits)."""
    text = clean_text(phone, max_length=30)
    if not text or not re.match(r"^[0-9+()\-\s]{6,30}$", text):
        return False
    digits = re.sub(r"\D", "", text)
    return 7 <= len(digits) <= 15


# In-memory datasets (also used to seed MongoDB if empty)
MEM_STUDENTS = [
    {
        "_id": "25Z295",
        "studentId": "25Z295",
        "name": "Sharvesh Mahi",
        "email": "25z295@psgitech.ac.in",
        "phone": "+91 98400 11295",
        "passwordHash": hash_password(DEMO_STUDENT_PASSWORD or secrets.token_urlsafe(32)),
        "department": "Computer Science & Engineering",
        "yearOfStudy": "1st Year",
        "dormLocation": "PSG iTech Campus Hostel Block A",
        "campus": "PSG Institute of Technology and Applied Research",
        "role": "STUDENT",
        "trustScore": 100,
        "activeLoansCount": 0
    },
    {
        "_id": "715521104001",
        "studentId": "715521104001",
        "name": "Karthik Raja",
        "email": "karthik.21cs@psgitech.ac.in",
        "phone": "+91 98400 22001",
        "passwordHash": hash_password(DEMO_STUDENT_PASSWORD or secrets.token_urlsafe(32)),
        "department": "Computer Science & Engineering",
        "yearOfStudy": "Junior",
        "dormLocation": "PSG iTech Boys Hostel",
        "campus": "PSG Institute of Technology and Applied Research",
        "role": "STUDENT",
        "trustScore": 98,
        "activeLoansCount": 2
    },
    {
        "_id": "715521104002",
        "studentId": "715521104002",
        "name": "Divya M.",
        "email": "divya.21ec@psgitech.ac.in",
        "phone": "+91 98400 33002",
        "passwordHash": hash_password(DEMO_STUDENT_PASSWORD or secrets.token_urlsafe(32)),
        "department": "Electronics & Communication Engineering",
        "yearOfStudy": "Sophomore",
        "dormLocation": "PSG iTech Girls Hostel",
        "campus": "PSG Institute of Technology and Applied Research",
        "role": "STUDENT",
        "trustScore": 99,
        "activeLoansCount": 1
    }
]

MEM_ITEMS = [
    {
        "_id": "item-1",
        "id": "item-1",
        "title": "TI-84 Plus CE Graphing Calculator",
        "category": "stationery",
        "categoryName": "Calculators & Lab",
        "dailyPrice": 50.00,
        "securityDeposit": 300.00,
        "condition": "Like New",
        "location": "Mech Block • 0.2 km",
        "campus": "PSG iTech Campus",
        "ownerId": "715521104002",
        "ownerName": "Divya M.",
        "ownerDept": "Sophomore • ECE Dept",
        "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuBM8VSzPWz6gX7VI2wzCYRejzZ-cxNpuaEF-mrtYyc4P20zvX2frfHkS75qBmQ7sNSciIYrMNM5VK1ZMyXi3W8ShFLb7o-zZNhhGqJAdNUbM3Z-b77r5tSXgdPIB6dd4mzmgFolQkHmrepl88pZ7AKd6OFrAyTCVunaRI3SuyVpfaalf0FqpiFIZkBil0Rq-_pMRvPb1lpO70yIbtS2D1m0a7Z9-EWNDqXSpV3R7YzR",
        "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuCwzEoEAOySUGjNOHtVUJfX4kzk2JoXBWr8O_2W6OlPBOBEyzFpdkwPF9maQ9UpdNsMNhfCUS2r3co300xpXSH1WgDkybFb8GNzCGFQuiKrPsYr-hmZl5O8hYxVk-y9cXuGdkTrUC89_-faqEUSw6bHHB1b3BkIkLNRObwI4vphIge7osJfNg6G1RmPKoEmOoxAuMrEH7yfzjBIMWa_DCjAE0B1vTF0hLqb6MycvIIR",
        "rating": "4.9 ★ (18 loans)",
        "description": "Pristine Python Edition color graphing calculator with backlit display and rechargeable battery. Essential for Engineering Math, Physics, and Lab exams. Sanitized and fully charged.",
        "available": True
    },
    {
        "_id": "item-2",
        "id": "item-2",
        "title": "Campbell Biology 12th Edition Hardcover",
        "category": "books",
        "categoryName": "Textbooks",
        "dailyPrice": 30.00,
        "securityDeposit": 200.00,
        "condition": "Pristine",
        "location": "CSE Block • 0.3 km",
        "campus": "PSG iTech Campus",
        "ownerId": "715521104001",
        "ownerName": "Karthik Raja",
        "ownerDept": "Junior • CSE Dept",
        "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
        "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHzF2ArCYVDUbZmI5k-3Auz7nNqDBA4WqGQ1_r8IIU8jjqDVNVlooZAqi6nibGOpGadYKu5ScBbKKgWnsr9ydHbAltNtedVgEgaBaLKfU3mkvw3s76vF3PLWIMxVCHi2JEtw-gzEwPkPdyYeDOy4DPmUnWHKUK0VL90C9XVINWLVarO1OgZfW830QxaJX5WPLTzllZIizBk3oRRULosxsviytiqWvpYwa3i9q7yI-j",
        "rating": "4.8 ★ (12 loans)",
        "description": "Clean hardcover edition without tears or missing pages. Has high-yield margin notes for biology and biochemistry coursework. Great for semester reviews.",
        "available": True
    },
    {
        "_id": "item-3",
        "id": "item-3",
        "title": "Sony WH-1000XM4 Noise Cancelling",
        "category": "tech",
        "categoryName": "Tech & Electronics",
        "dailyPrice": 60.00,
        "securityDeposit": 400.00,
        "condition": "Excellent",
        "location": "Central Library • 0.1 km",
        "campus": "PSG iTech Campus",
        "ownerId": "25Z295",
        "ownerName": "Sharvesh Mahi",
        "ownerDept": "1st Year • CSE Dept",
        "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuDPK1wGgvcZzVIu09lEX1h_MzqjkCm43D_4Gld-fUyrR9IOfggN9H8l2cyKaQMsay2y4vJ_DLobml1FlJd0Ala2y1FLIQdTzFyYBHhYNvgc9JS5svtcYjYuHmxH000cZoAk7B2YX9tpxlpUfQjdI0l-7qkb2jzCotbZSLOEbmhCufoSzHFGW-2d8lPok-lStjxEb0oy5NWMdVzckaT0O6ERhshe9ub0pDFa3hvavx5J",
        "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuBkiquaYFgXakbP2mClmnfb7Va95cC2ekw5VVdqNTX6jzILz4X_lJKi8F7grlVAE-D9QiYeYNyjJfBNCInzQNdNbTdhKGLlWQxRmNdrhjptxFxbyvnmSlNKt4noiBYmHuVR9dyRrTDmvqLd6x9ViR5S6d4p7abPPi0nVk1HllDhaVaucdQJVULxFyeoPQ-MIcFK2c62h2EK7TIpoWfeB3YsuX_Kqfn_xkqORUID6qZG",
        "rating": "5.0 ★ (26 loans)",
        "description": "Active noise cancellation over-ear headphones. Unrivaled for deep focus in Central Library or dormitory study halls. 30-hour battery life.",
        "available": True
    },
    {
        "_id": "item-4",
        "id": "item-4",
        "title": "Heavy Duty Kryptonite U-Lock with Cable",
        "category": "sports",
        "categoryName": "Sports & Outdoor",
        "dailyPrice": 20.00,
        "securityDeposit": 150.00,
        "condition": "Sturdy",
        "location": "College Quadrangle • 0.2 km",
        "campus": "PSG iTech Campus",
        "ownerId": "715521104001",
        "ownerName": "Karthik Raja",
        "ownerDept": "Junior • CSE Dept",
        "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
        "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuD8LJ5er6DzREDNtgIhPowV_RLu0QJ7E6WBjDYlDPkdDFUGYbzCXQAQv_5mxifD6texvT-FrKICtTvmQPgroK95DNV0jUrDaWNxDd1l-3csq3mAfU02tGPToGD5bh2P1lSXX_gF5WvYXB2pghXiBoURCAhoQSxeyhMiSl8mPumqbg16PpeRys7ZfhVcdEAALS07xemOog2RtG5rnYGZ1_D_opGEsZdWgn7fzbV_BbD3",
        "rating": "4.9 ★ (14 loans)",
        "description": "Hardened steel bicycle lock with 4ft looped steel cable. Includes 2 keys. Essential for keeping bikes and e-scooters protected on campus.",
        "available": True
    },
    {
        "_id": "item-5",
        "id": "item-5",
        "title": "Java Software Solutions (8th Ed)",
        "category": "books",
        "categoryName": "Textbooks",
        "dailyPrice": 30.00,
        "securityDeposit": 200.00,
        "condition": "Like New",
        "location": "IT Block • 0.2 km",
        "campus": "PSG iTech Campus",
        "ownerId": "715521104001",
        "ownerName": "Karthik Raja",
        "ownerDept": "Junior • CSE Dept",
        "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuDPK1wGgvcZzVIu09lEX1h_MzqjkCm43D_4Gld-fUyrR9IOfggN9H8l2cyKaQMsay2y4vJ_DLobml1FlJd0Ala2y1FLIQdTzFyYBHhYNvgc9JS5svtcYjYuHmxH000cZoAk7B2YX9tpxlpUfQjdI0l-7qkb2jzCotbZSLOEbmhCufoSzHFGW-2d8lPok-lStjxEb0oy5NWMdVzckaT0O6ERhshe9ub0pDFa3hvavx5J",
        "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuDM-3UvkaYlTm0DmafG2spCGujBwntxSSe3OWHJz2R8uZKO50r7sHrasD3L-RWNH5rIg8TcLJD2yYvO4w8Abv0xkONRIw6-ue9a5vRe7wg2Zt8vo1anc-i4vu_mL-m7Tfd8tYeYSzOnTUdi2JqAxO67ILac5J9NFvaF0b6rMr6D2wQUv_sCTRorNe4KdsJtEdMqwUsvQHfiCUTDcJlkq0kCviYFnDezQVCzX1cNNSRq",
        "rating": "4.7 ★ (9 loans)",
        "description": "Foundations of program design, object-oriented concepts, recursion, and data structures. Recommended for programming and data structures lab coursework.",
        "available": True
    },
    {
        "_id": "item-6",
        "id": "item-6",
        "title": "Logitech MX Master 3S Wireless Mouse",
        "category": "tech",
        "categoryName": "Tech & Electronics",
        "dailyPrice": 40.00,
        "securityDeposit": 300.00,
        "condition": "Pristine",
        "location": "Civil Block • 0.3 km",
        "campus": "PSG iTech Campus",
        "ownerId": "25Z295",
        "ownerName": "Sharvesh Mahi",
        "ownerDept": "1st Year • CSE Dept",
        "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
        "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuD7gwQjV590U9vx14Fk3gWAVGNeM94g7uvPbrLTk2sSK8gny8hVVMT7_0_gm89wFpynlso1Q9OX3izu6Wd4PNJLwwEJNRNjDD2aJQl_5o0aKz5Q1ma_k-mNZwBS7eSiO6fd43lyYEJQMNYJTyVboZBYo00lgRiaz0tR2Zw_aomqYqDQpCp93tw6nEGJjG_rCBVbXdJ1kTE1eCchh_pJHvktAPkVxwhBPFeAVLkhixo7",
        "rating": "4.9 ★ (19 loans)",
        "description": "Ergonomic quiet click mouse with electromagnetic MagSpeed scroll wheel. Perfect for CAD lab, coding, Figma, and design projects.",
        "available": True
    }
]

MEM_LOANS = []
MEM_MESSAGES = {}
DATA_LOCK = threading.RLock()
AGREED_LOAN_STATUSES = {"ACCEPTED", "ACTIVE", "LENT OUT"}

# Try importing pymongo; fallback to in-memory store if not installed
try:
    from pymongo import MongoClient
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
    mongo_client.server_info()
    db_name = os.environ.get("MONGO_DB_NAME", "lend")
    db = mongo_client[db_name]
    HAS_MONGO = True
    print(f"[*] Successfully connected to MongoDB at {mongo_uri} ({db_name})")

    # Seed initial demo members only when explicitly enabled with a password.
    if SEED_DEMO_DATA and DEMO_STUDENT_PASSWORD:
        for student in MEM_STUDENTS:
            try:
                if not db.students.find_one({"email": student["email"]}):
                    db.students.insert_one(dict(student))
            except Exception:
                pass
        print("[*] Demo student accounts seeded (SEED_DEMO_DATA=true).", flush=True)
    else:
        # Never expose in-memory demo accounts with known/random credentials.
        MEM_STUDENTS.clear()

    # Migrate legacy plaintext password values to PBKDF2 on first run.
    try:
        for doc in db.students.find({}, {"passwordHash": 1, "password": 1}):
            stored = doc.get("passwordHash") or doc.get("password")
            if not stored:
                continue
            stored = str(stored)
            looks_hashed = (
                stored.startswith("pbkdf2_sha256$")
                or stored.startswith("$2")
                or "$" in stored
            )
            if not looks_hashed:
                db.students.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"passwordHash": hash_password(stored)},
                     "$unset": {"password": ""}},
                )
                print(f"[*] Migrated legacy plaintext password for {doc.get('_id')}", flush=True)
    except Exception as migration_error:
        print(f"[!] Password migration notice: {migration_error}", flush=True)

    # Seed initial items if database collection is empty
    if db.items.count_documents({}) == 0:
        for item in MEM_ITEMS:
            try:
                db.items.insert_one(dict(item))
            except Exception:
                pass
        print(f"[*] Seeded {len(MEM_ITEMS)} initial catalog items into '{db_name}' database.")
except Exception as e:
    HAS_MONGO = False
    print(f"[!] MongoDB not reachable via pymongo ({e}). Running with in-memory fallback store.")
    if not (SEED_DEMO_DATA and DEMO_STUDENT_PASSWORD):
        MEM_STUDENTS.clear()


def find_student_record(identifier):
    """Find a student record by studentId, email, or _id; never return password fields."""
    ident = str(identifier or "").strip()
    if not ident:
        return None
    doc = None
    if HAS_MONGO:
        doc = db.students.find_one({
            "$or": [
                {"studentId": {"$regex": f"^{re.escape(ident)}$", "$options": "i"}},
                {"email": {"$regex": f"^{re.escape(ident)}$", "$options": "i"}},
                {"_id": ident}
            ]
        })
    else:
        ident_lower = ident.lower()
        with DATA_LOCK:
            for s in MEM_STUDENTS:
                if (str(s.get("studentId", "")).lower() == ident_lower
                        or str(s.get("email", "")).lower() == ident_lower
                        or str(s.get("_id", "")).lower() == ident_lower):
                    doc = dict(s)
                    break
    if not doc:
        return None
    clean = dict(doc)
    clean["id"] = str(clean.get("_id", clean.get("studentId", "")))
    clean.pop("passwordHash", None)
    clean.pop("password", None)
    clean.pop("_id", None)
    return clean


def find_loan_record(loan_id):
    """Look up a loan document by _id or id."""
    lid = str(loan_id or "").strip()
    if not lid:
        return None
    if HAS_MONGO:
        doc = db.loans.find_one({"$or": [{"_id": lid}, {"id": lid}]})
        return dict(doc) if doc else None
    with DATA_LOCK:
        for l in MEM_LOANS:
            if l.get("id") == lid or l.get("_id") == lid:
                return dict(l)
    return None


def enrich_loan_for_viewer(loan_doc, viewer_role=None):
    """Normalize loan output and attach peer phone only after both parties agree."""
    d = dict(loan_doc)
    d["id"] = str(d.get("_id", d.get("id", "")))
    d.pop("_id", None)
    status = str(d.get("status", "PENDING")).upper()
    agreed = status in AGREED_LOAN_STATUSES
    d["status"] = status
    d["chatUnlocked"] = agreed

    if agreed:
        lender_doc = find_student_record(d.get("lenderId") or d.get("lenderEmail"))
        borrower_doc = find_student_record(d.get("borrowerId") or d.get("borrowerEmail"))
        lender_phone = (lender_doc.get("phone") if lender_doc else "") or d.get("lenderPhone", "")
        borrower_phone = (borrower_doc.get("phone") if borrower_doc else "") or d.get("borrowerPhone", "")
        d["lenderPhone"] = lender_phone
        d["borrowerPhone"] = borrower_phone
        if viewer_role == "borrower":
            d["peerPhone"] = lender_phone
            d["peerName"] = d.get("lenderName", "")
            d["peerDept"] = d.get("lenderDept", "")
        elif viewer_role == "lender":
            d["peerPhone"] = borrower_phone
            d["peerName"] = d.get("borrowerName", "")
            d["peerDept"] = d.get("borrowerDept", "")
    else:
        d["lenderPhone"] = ""
        d["borrowerPhone"] = ""
        d["peerPhone"] = ""
    return d


def get_loan_messages(loan_id):
    """Fetch ordered chat messages for an agreed loan."""
    lid = str(loan_id or "").strip()
    if HAS_MONGO:
        docs = list(db.messages.find({"loanId": lid}).sort("createdAt", 1))
        msgs = []
        for m in docs:
            item = dict(m)
            item["id"] = str(item.get("_id", item.get("id", "")))
            item.pop("_id", None)
            msgs.append(item)
        return msgs
    with DATA_LOCK:
        return [dict(m) for m in MEM_MESSAGES.get(lid, [])]


def append_loan_message(loan_id, msg_doc):
    """Persist a chat message for an agreed loan."""
    lid = str(loan_id or "").strip()
    stored = dict(msg_doc)
    if HAS_MONGO:
        db.messages.insert_one(dict(stored))
        stored.pop("_id", None)
    else:
        with DATA_LOCK:
            MEM_MESSAGES.setdefault(lid, []).append(stored)
    return stored


def validate_psgitech_email(raw_email):
    if not raw_email or not str(raw_email).strip():
        return False, "College email cannot be empty"
    email = str(raw_email).strip().lower()
    if not re.match(r"^[a-zA-Z0-9._%+-]+@psgitech\.ac\.in$", email):
        return False, f"Access restricted: Only official PSG iTech email addresses (@{COLLEGE_DOMAIN}) are permitted. Personal emails (Gmail, Yahoo, Outlook) are not allowed."
    return True, email


def send_otp_email(to_email, otp):
    smtp_host = os.environ.get("SPRING_MAIL_HOST", os.environ.get("SMTP_HOST", "smtp.gmail.com"))
    smtp_port = int(os.environ.get("SPRING_MAIL_PORT", os.environ.get("SMTP_PORT", 587)))
    smtp_user = os.environ.get("SPRING_MAIL_USERNAME", os.environ.get("SMTP_USER", ""))
    smtp_pass = os.environ.get("SPRING_MAIL_PASSWORD", os.environ.get("SMTP_PASS", ""))

    if smtp_user and smtp_pass:
        try:
            sender_email = os.environ.get(
                "SMTP_FROM", os.environ.get("SENDER_EMAIL", smtp_user or f"no-reply@{COLLEGE_DOMAIN}")
            )
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Your PSG iTech Campus Lend Verification Code: {otp}"
            msg["From"] = f"PSG iTech Campus Lend <{sender_email}>"
            msg["To"] = to_email

            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 520px; margin: auto; padding: 24px; border: 1px solid #e8edff; border-radius: 12px; background: #ffffff;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="display: inline-block; background: #002753; color: #ffffff; padding: 6px 14px; border-radius: 8px; font-weight: bold; font-size: 14px;">
                        PSG iTech Campus Lend
                    </div>
                    <p style="color: #0051d5; font-size: 11px; margin-top: 4px; font-weight: bold;">PSG INSTITUTE OF TECHNOLOGY AND APPLIED RESEARCH</p>
                </div>
                <h3 style="color: #002753; text-align: center;">Verify Your Official College Email</h3>
                <p style="text-align: center; color: #495057; font-size: 13px;">Use the 6-digit OTP code below to authenticate your student registration for <strong>{to_email}</strong>:</p>
                <div style="text-align: center; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #002753; padding: 16px; background: #f1f4fd; border: 1px dashed #0051d5; border-radius: 10px; margin: 20px 0;">
                    {otp}
                </div>
                <p style="color: #ba1a1a; font-size: 12px; text-align: center; font-weight: bold;">Valid for 5 minutes only • Single use • Max 5 attempts</p>
            </div>
            """
            msg.attach(MIMEText(html, "html"))
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_pass)
                server.sendmail(sender_email, to_email, msg.as_string())
            print(f"[*] OTP email dispatched via SMTP to {to_email}", flush=True)
            return True
        except Exception as e:
            print(f"[!] SMTP dispatch failed: {e}", flush=True)
            return False

    # Development fallback only: never log OTP codes when email delivery is configured.
    print("\n" + "=" * 65, flush=True)
    print(" [PSG iTech College OTP - DEVELOPMENT FALLBACK]", flush=True)
    print(f" Recipient: {to_email}", flush=True)
    print(f" OTP Code:  {otp}  (Valid for 5 minutes, single use)", flush=True)
    print(" SMTP is not configured; this code is printed to the server console only.", flush=True)
    print("=" * 65 + "\n", flush=True)
    return True





class RequestTooLarge(Exception):
    pass


class CampusLendAPIHandler(BaseHTTPRequestHandler):
    timeout = 30
    server_version = "CampusLend"
    sys_version = ""

    # ---- Security headers & CORS ----
    def _cors_origin(self):
        origin = (self.headers.get("Origin") or "").strip()
        if not origin:
            return None
        origin = origin.rstrip("/")
        host = (self.headers.get("Host") or "").strip().lower()
        if host and origin.lower() in (f"http://{host}", f"https://{host}"):
            return origin
        if origin in ALLOWED_ORIGINS:
            return origin
        if origin == "null" and ALLOW_FILE_ORIGIN:
            return "null"
        return None

    def _send_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        self.send_header("Content-Security-Policy", SECURITY_CSP)
        origin = self._cors_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, HEAD")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept")
            self.send_header("Access-Control-Max-Age", "600")

    # Send responses with proper HTTP framing and CORS headers
    def _send_json(self, data, status=200):
        try:
            payload = json.dumps(data, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self._send_security_headers()
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:
            print(f"[!] Error in _send_json: {e}", flush=True)

    def do_OPTIONS(self):
        try:
            self.send_response(204)
            self._send_security_headers()
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
        except Exception:
            pass

    def do_HEAD(self):
        try:
            self.send_response(200)
            self._send_security_headers()
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
        except Exception:
            pass

    def _read_json(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0) or 0)
        except (TypeError, ValueError):
            raise RequestTooLarge("Invalid Content-Length")
        if content_length <= 0:
            return {}
        if content_length > MAX_BODY_BYTES:
            raise RequestTooLarge("Request body too large")
        try:
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
        except Exception as e:
            print(f"[!] Warning reading request JSON: {e}", flush=True)
            return {}
        return data if isinstance(data, dict) else {}

    # ---- Authentication helpers ----
    def _auth_payload(self):
        header = self.headers.get("Authorization", "")
        if not header.lower().startswith("bearer "):
            return None
        return verify_auth_token(header[7:].strip())

    def _require_auth(self):
        payload = self._auth_payload()
        if not payload:
            self._send_json({"error": "Authentication required. Please log in."}, 401)
        return payload

    @staticmethod
    def _identity_matches(payload, identifier):
        ident = str(identifier or "").strip().lower()
        if not ident or not payload:
            return False
        candidates = {
            str(payload.get("sub", "")).strip().lower(),
            str(payload.get("email", "")).strip().lower(),
        }
        candidates.discard("")
        return ident in candidates

    def _loan_viewer_role(self, auth, loan_doc):
        """Return 'borrower', 'lender', or None depending on authenticated party."""
        if not auth or not loan_doc:
            return None
        if self._identity_matches(auth, loan_doc.get("borrowerId")) or self._identity_matches(auth, loan_doc.get("borrowerEmail")):
            return "borrower"
        if self._identity_matches(auth, loan_doc.get("lenderId")) or self._identity_matches(auth, loan_doc.get("lenderEmail")):
            return "lender"
        return None

    def _authorize_agreed_loan_chat(self, auth, loan_id):
        """Load loan, verify caller is a party, and ensure both parties agreed."""
        loan_doc = find_loan_record(loan_id)
        if not loan_doc:
            self._send_json({"error": "Loan not found."}, 404)
            return None, None
        role = self._loan_viewer_role(auth, loan_doc)
        if not role:
            self._send_json({"error": "You are not allowed to access this conversation."}, 403)
            return None, None
        if str(loan_doc.get("status", "")).upper() not in AGREED_LOAN_STATUSES:
            self._send_json({"error": "Chat and calling unlock only after both parties agree on the request."}, 403)
            return None, None
        return loan_doc, role

    def _client_ip(self):
        return self.client_address[0] if self.client_address else "unknown"

    # ---- Static file allowlist (never serves dotfiles / source / configs) ----
    def _resolve_static(self, path):
        clean_path = urllib.parse.unquote(path).lstrip("/") or "index.html"
        parts = [p for p in clean_path.replace("\\", "/").split("/") if p not in ("", ".")]
        if any(p == ".." or p.startswith(".") for p in parts):
            return None
        if len(parts) == 1 and parts[0] in STATIC_ALLOWLIST:
            candidate = parts[0]
        elif parts and parts[0] in STATIC_DIRS and len(parts) >= 2:
            candidate = os.path.join(*parts)
        else:
            candidate = "index.html"  # SPA fallback (always a fixed, safe file)
        file_path = os.path.abspath(os.path.join(STATIC_DIR, candidate))
        try:
            if os.path.commonpath([STATIC_DIR, file_path]) != STATIC_DIR:
                return os.path.join(STATIC_DIR, "index.html")
        except ValueError:
            return os.path.join(STATIC_DIR, "index.html")
        if not os.path.isfile(file_path):
            return os.path.join(STATIC_DIR, "index.html")
        return file_path

    # ================= GET ENDPOINTS =================
    def do_GET(self):
        try:
            self._handle_get()
        except Exception as e:
            print(f"[!] Unhandled error in GET {self.path}: {e}", flush=True)
            self._send_json({"error": "Internal server error"}, 500)

    def _handle_get(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # Serve static web frontend files (strict allowlist: index.html, translations.js, assets/)
        if not path.startswith("/api"):
            file_path = self._resolve_static(path)
            if not file_path:
                self._send_json({"error": "Not found"}, 404)
                return

            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime = {
                    ".html": "text/html; charset=utf-8",
                    ".js": "application/javascript; charset=utf-8",
                    ".css": "text/css; charset=utf-8",
                    ".svg": "image/svg+xml",
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".json": "application/json"
                }.get(ext, "application/octet-stream")

                try:
                    file_size = os.path.getsize(file_path)
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(file_size))
                    self._send_security_headers()
                    self.send_header("Connection", "close")
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        while chunk := f.read(65536):
                            self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
                except Exception as e:
                    print(f"[!] Error serving static file {file_path}: {e}", flush=True)
                return

        # 1. GET /api/items
        if path == "/api/items" or path == "/api/items/":
            items = []
            if HAS_MONGO:
                query = {}
                cat = params.get("category", [None])[0]
                if cat and cat != "all":
                    query["category"] = cat.lower()

                avail = params.get("availableOnly", [None])[0]
                if avail == "true":
                    query["available"] = True

                docs = list(db.items.find(query))
                for d in docs:
                    d["id"] = str(d.get("_id", d.get("id", "")))
                    if "_id" in d:
                        del d["_id"]
                    items.append(d)
            else:
                items = MEM_ITEMS

            search = params.get("search", [None])[0]
            if search:
                s_lower = search.lower()
                items = [it for it in items if s_lower in it.get("title", "").lower() or s_lower in it.get("description", "").lower()]

            self._send_json(items)
            return

        # 2. GET /api/items/{id}
        if path.startswith("/api/items/"):
            item_id = path.replace("/api/items/", "")
            if HAS_MONGO:
                doc = db.items.find_one({"_id": item_id}) or db.items.find_one({"id": item_id})
                if doc:
                    doc["id"] = str(doc.get("_id", doc.get("id", "")))
                    if "_id" in doc:
                        del doc["_id"]
                    self._send_json(doc)
                    return
            else:
                for it in MEM_ITEMS:
                    if it.get("id") == item_id or it.get("_id") == item_id:
                        self._send_json(it)
                        return
            self._send_json({"error": "Item not found"}, 404)
            return

        # 3. GET /api/students/{id} - authenticated, self only
        if path.startswith("/api/students/"):
            s_id = path.replace("/api/students/", "").strip()
            auth = self._require_auth()
            if not auth:
                return
            if not self._identity_matches(auth, s_id):
                self._send_json({"error": "You are not allowed to view this profile."}, 403)
                return
            if HAS_MONGO:
                student = db.students.find_one({
                    "$or": [
                        {"studentId": {"$regex": f"^{re.escape(s_id)}$", "$options": "i"}},
                        {"email": {"$regex": f"^{re.escape(s_id)}$", "$options": "i"}},
                        {"_id": s_id}
                    ]
                })
                if student:
                    student["id"] = str(student.get("_id", student.get("studentId", "")))
                    if "passwordHash" in student:
                        del student["passwordHash"]
                    if "password" in student:
                        del student["password"]
                    if "_id" in student:
                        del student["_id"]
                    self._send_json(student)
                    return
            else:
                for s in MEM_STUDENTS:
                    if s.get("studentId", "").lower() == s_id.lower() or s.get("email", "").lower() == s_id.lower():
                        clean = dict(s)
                        if "passwordHash" in clean:
                            del clean["passwordHash"]
                        if "password" in clean:
                            del clean["password"]
                        self._send_json(clean)
                        return
            self._send_json({"error": "Student not found"}, 404)
            return

        # 4. GET /api/loans/{loan_id}/messages - authenticated party only, agreed loans only
        if path.startswith("/api/loans/") and path.endswith("/messages"):
            loan_id = path[len("/api/loans/"):-len("/messages")].strip("/")
            auth = self._require_auth()
            if not auth:
                return
            loan_doc, role = self._authorize_agreed_loan_chat(auth, loan_id)
            if not loan_doc:
                return
            enriched = enrich_loan_for_viewer(loan_doc, viewer_role=role)
            self._send_json({
                "loanId": enriched["id"],
                "itemTitle": enriched.get("itemTitle", "Campus Item"),
                "status": enriched["status"],
                "chatUnlocked": True,
                "peerName": enriched.get("peerName", ""),
                "peerDept": enriched.get("peerDept", ""),
                "peerPhone": enriched.get("peerPhone", ""),
                "messages": get_loan_messages(enriched["id"])
            })
            return

        # 5. GET /api/loans/borrower/{id} - authenticated, self only
        if path.startswith("/api/loans/borrower/"):
            b_id = path.replace("/api/loans/borrower/", "").strip()
            auth = self._require_auth()
            if not auth:
                return
            if not self._identity_matches(auth, b_id):
                self._send_json({"error": "You are not allowed to view these loans."}, 403)
                return
            loans = []
            if HAS_MONGO:
                docs = list(db.loans.find({
                    "$or": [
                        {"borrowerId": {"$regex": f"^{re.escape(b_id)}$", "$options": "i"}},
                        {"borrowerEmail": {"$regex": f"^{re.escape(b_id)}$", "$options": "i"}}
                    ]
                }))
            else:
                with DATA_LOCK:
                    docs = [l for l in MEM_LOANS if l.get("borrowerId", "").lower() == b_id.lower() or l.get("borrowerEmail", "").lower() == b_id.lower()]
            loans = [enrich_loan_for_viewer(d, viewer_role="borrower") for d in docs]
            self._send_json(loans)
            return

        # 6. GET /api/loans/lender/{id} - authenticated, self only
        if path.startswith("/api/loans/lender/"):
            l_id = path.replace("/api/loans/lender/", "").strip()
            auth = self._require_auth()
            if not auth:
                return
            if not self._identity_matches(auth, l_id):
                self._send_json({"error": "You are not allowed to view these loans."}, 403)
                return
            loans = []
            if HAS_MONGO:
                docs = list(db.loans.find({
                    "$or": [
                        {"lenderId": {"$regex": f"^{re.escape(l_id)}$", "$options": "i"}},
                        {"lenderEmail": {"$regex": f"^{re.escape(l_id)}$", "$options": "i"}}
                    ]
                }))
            else:
                with DATA_LOCK:
                    docs = [l for l in MEM_LOANS if l.get("lenderId", "").lower() == l_id.lower() or l.get("lenderEmail", "").lower() == l_id.lower()]
            loans = [enrich_loan_for_viewer(d, viewer_role="lender") for d in docs]
            self._send_json(loans)
            return

        self._send_json({"error": "Route not found", "path": path}, 404)

    # ================= POST ENDPOINTS =================
    def do_POST(self):
        try:
            self._handle_post()
        except RequestTooLarge:
            self._send_json({"error": "Request body is too large."}, 413)
        except Exception as e:
            print(f"[!] Unhandled error in POST {self.path}: {e}", flush=True)
            self._send_json({"error": "Internal server error"}, 500)

    def _handle_post(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json()

        # 1. POST /api/auth/send-otp
        if path == "/api/auth/send-otp":
            valid, res = validate_psgitech_email(body.get("email"))
            if not valid:
                self._send_json({"error": res}, 400)
                return

            email = res

            # Per-IP abuse protection (password/OTP email bombing)
            if not rate_limit_allow(OTP_REQUEST_ATTEMPTS, self._client_ip(),
                                    OTP_IP_WINDOW_SECONDS, OTP_IP_MAX_REQUESTS):
                self._send_json({"error": "Too many OTP requests from this address. Please try again later."}, 429)
                return

            # Duplicate check (case-insensitive)
            if HAS_MONGO:
                if db.students.find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}}):
                    self._send_json({"error": f"An account with {email} is already registered. Please log in."}, 400)
                    return
            else:
                if any(s.get("email", "").lower() == email for s in MEM_STUDENTS):
                    self._send_json({"error": f"An account with {email} is already registered. Please log in."}, 400)
                    return

            purge_expired_otp_entries()
            now = time.time()
            with OTP_LOCK:
                # Rate limiting / 60s cooldown check
                if email in OTP_STORE:
                    last_sent = OTP_STORE[email].get("last_sent", 0)
                    elapsed = now - last_sent
                    if elapsed < OTP_COOLDOWN_SECONDS:
                        wait_time = int(OTP_COOLDOWN_SECONDS - elapsed)
                        self._send_json({"error": f"Please wait {wait_time} seconds before requesting a new OTP."}, 400)
                        return

                # Generate random 6-digit OTP
                otp_code = str(secrets.randbelow(900000) + 100000)
                salt = secrets.token_hex(16)
                otp_hash = hashlib.sha256(f"{otp_code}:{salt}".encode()).hexdigest()

                OTP_STORE[email] = {
                    "hash": otp_hash,
                    "salt": salt,
                    "expires_at": now + OTP_EXPIRY_SECONDS,
                    "attempts": 0,
                    "last_sent": now,
                    "verified": False,
                    "verification_token": None,
                    "verified_at": 0,
                }

            rate_limit_hit(OTP_REQUEST_ATTEMPTS, self._client_ip(), OTP_IP_WINDOW_SECONDS)

            # Dispatch email (or log to terminal)
            send_otp_email(email, otp_code)

            self._send_json({
                "success": True,
                "message": f"A 6-digit OTP has been sent to your official PSG iTech email ({email}). It expires in 5 minutes.",
                "email": email
            })
            return

        # 2. POST /api/auth/verify-otp
        if path == "/api/auth/verify-otp":
            valid, res = validate_psgitech_email(body.get("email"))
            if not valid:
                self._send_json({"error": res}, 400)
                return

            email = res
            otp_code = str(body.get("otp", "")).strip()

            if not re.match(r"^\d{6}$", otp_code):
                self._send_json({"error": "OTP must be exactly 6 digits."}, 400)
                return

            purge_expired_otp_entries()
            with OTP_LOCK:
                record = OTP_STORE.get(email)
                if not record:
                    self._send_json({"error": f"No active OTP request found for {email}. Please request an OTP first."}, 400)
                    return

                now = time.time()

                # Already verified check (verification token itself expires)
                if record.get("verified") and record.get("verification_token"):
                    if now <= record.get("verified_at", 0) + VERIFICATION_TOKEN_TTL:
                        self._send_json({
                            "success": True,
                            "verified": True,
                            "email": email,
                            "verificationToken": record["verification_token"],
                            "message": "College email already verified."
                        })
                        return
                    OTP_STORE.pop(email, None)
                    self._send_json({"error": "Verification expired. Please request a new OTP."}, 400)
                    return

                # Max attempts check
                if record.get("attempts", 0) >= OTP_MAX_ATTEMPTS:
                    self._send_json({"error": f"Maximum OTP verification attempts ({OTP_MAX_ATTEMPTS}) exceeded. Please request a new OTP."}, 400)
                    return

                # Expiration check
                if now > record.get("expires_at", 0):
                    self._send_json({"error": "OTP has expired (valid for 5 minutes). Please request a new OTP."}, 400)
                    return

                # Compare SHA-256 hashes in constant time
                cand_hash = hashlib.sha256(f"{otp_code}:{record['salt']}".encode()).hexdigest()
                if record.get("hash") is None or not hmac.compare_digest(cand_hash, record.get("hash", "")):
                    record["attempts"] = record.get("attempts", 0) + 1
                    remaining = max(0, OTP_MAX_ATTEMPTS - record["attempts"])
                    if remaining == 0:
                        self._send_json({"error": "Incorrect OTP. Maximum attempts reached. Please request a new OTP."}, 400)
                        return
                    self._send_json({"error": f"Incorrect OTP. {remaining} attempt(s) remaining."}, 400)
                    return

                # Verification successful (Single-use invalidation of OTP)
                v_token = secrets.token_hex(24)
                record["verified"] = True
                record["verification_token"] = v_token
                record["verified_at"] = now
                record["hash"] = None  # Invalidate OTP hash for single-use guarantee
                record["attempts"] = 0

            print(f"[+] Successfully verified OTP for PSG iTech student: {email}", flush=True)
            self._send_json({
                "success": True,
                "verified": True,
                "email": email,
                "verificationToken": v_token,
                "message": "College email verified successfully."
            })
            return

        # 3. POST /api/auth/register
        if path == "/api/auth/register":
            valid, res = validate_psgitech_email(body.get("email"))
            if not valid:
                self._send_json({"error": res}, 400)
                return
            email = res

            v_token = str(body.get("verificationToken", "")).strip()
            purge_expired_otp_entries()
            with OTP_LOCK:
                record = OTP_STORE.get(email)
                token_ok = bool(
                    record
                    and record.get("verified")
                    and record.get("verification_token")
                    and v_token
                    and hmac.compare_digest(str(record.get("verification_token")), v_token)
                    and time.time() <= record.get("verified_at", 0) + VERIFICATION_TOKEN_TTL
                )
            if not token_ok:
                self._send_json({"error": "Email verification required or expired. Please verify your PSG iTech email with OTP again."}, 400)
                return

            student_id = clean_text(body.get("studentId"), max_length=40).upper()
            if not student_id:
                self._send_json({"error": "Student ID / Roll Number is required."}, 400)
                return
            if not re.match(r"^[A-Z0-9._-]{3,40}$", student_id):
                self._send_json({"error": "Student ID may only contain letters, digits, dots, dashes and underscores."}, 400)
                return

            name = clean_text(body.get("name"), max_length=120)
            if len(name) < 2:
                self._send_json({"error": "Please enter a valid student name."}, 400)
                return

            phone = clean_text(body.get("phone"), max_length=30)
            if not is_valid_phone(phone):
                self._send_json({"error": "Please provide a valid phone number."}, 400)
                return

            raw_password = str(body.get("password", ""))
            if len(raw_password) < 8:
                self._send_json({"error": "Password must be at least 8 characters long."}, 400)
                return
            if len(raw_password) > 200:
                self._send_json({"error": "Password is too long."}, 400)
                return

            # Duplicate email or studentId check (case-insensitive)
            if HAS_MONGO:
                if db.students.find_one({
                    "$or": [
                        {"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}},
                        {"studentId": {"$regex": f"^{re.escape(student_id)}$", "$options": "i"}}
                    ]
                }):
                    self._send_json({"error": f"An account with {email} or ID {student_id} is already registered. Please log in."}, 400)
                    return
            else:
                if any(s.get("email", "").lower() == email or s.get("studentId", "").lower() == student_id.lower() for s in MEM_STUDENTS):
                    self._send_json({"error": f"An account with {email} or ID {student_id} is already registered. Please log in."}, 400)
                    return

            hashed_pwd = hash_password(raw_password)

            new_student = {
                "_id": student_id,
                "studentId": student_id,
                "name": name,
                "email": email,
                "phone": phone,
                "passwordHash": hashed_pwd,
                "department": clean_text(body.get("department"), max_length=120, default="Computer Science & Engineering"),
                "yearOfStudy": clean_text(body.get("yearOfStudy"), max_length=40, default="1st Year"),
                "dormLocation": clean_text(body.get("dormLocation"), max_length=160, default="Campus Hostel Block A"),
                "campus": "PSG Institute of Technology and Applied Research",
                "role": "STUDENT",
                "trustScore": 100,
                "activeLoansCount": 0
            }

            if HAS_MONGO:
                try:
                    db.students.insert_one(dict(new_student))
                    if "_id" in new_student:
                        del new_student["_id"]
                except Exception as e:
                    print(f"[!] Registration database error: {e}", flush=True)
                    self._send_json({"error": "Registration failed. Please try again later."}, 500)
                    return
            else:
                MEM_STUDENTS.append(new_student)

            # Purge single-use verification token
            with OTP_LOCK:
                OTP_STORE.pop(email, None)

            token = create_auth_token({**new_student, "studentId": student_id, "email": email})
            clean_student = {k: v for k, v in new_student.items() if k != "passwordHash"}

            print(f"[+] Successfully registered new PSG iTech student: {new_student['name']} ({email})", flush=True)
            self._send_json({
                "token": token,
                "type": "Bearer",
                "student": clean_student,
                "message": "Student account registered successfully"
            }, 201)
            return

        # 4. POST /api/auth/login
        if path == "/api/auth/login":
            email_or_id = clean_text(body.get("email"), max_length=200)
            password = str(body.get("password", ""))

            if not email_or_id or not password:
                self._send_json({"error": "College email/Student ID and password are required."}, 400)
                return

            # Brute-force protection per client address
            client_ip = self._client_ip()
            if not rate_limit_allow(LOGIN_ATTEMPTS, client_ip, LOGIN_WINDOW_SECONDS, LOGIN_MAX_ATTEMPTS):
                self._send_json({"error": "Too many failed login attempts. Please try again in 15 minutes."}, 429)
                return

            if "@" in email_or_id:
                valid, res = validate_psgitech_email(email_or_id)
                if not valid:
                    self._send_json({"error": res}, 400)
                    return
                email_or_id = res

            student = None
            if HAS_MONGO:
                try:
                    query_conditions = [
                        {"email": {"$regex": f"^{re.escape(email_or_id)}$", "$options": "i"}},
                        {"studentId": {"$regex": f"^{re.escape(email_or_id)}$", "$options": "i"}},
                        {"_id": email_or_id}
                    ]
                    try:
                        from bson import ObjectId
                        if ObjectId.is_valid(email_or_id):
                            query_conditions.append({"_id": ObjectId(email_or_id)})
                    except Exception:
                        pass
                    student = db.students.find_one({"$or": query_conditions})
                except Exception as mongo_err:
                    print(f"[!] MongoDB student lookup notice: {mongo_err}", flush=True)
                    student = None

            # Fallback to in-memory store if not found in MongoDB
            if not student:
                for s in MEM_STUDENTS:
                    if (s.get("email", "").lower() == email_or_id.lower() or 
                        s.get("studentId", "").lower() == email_or_id.lower() or 
                        str(s.get("_id", "")).lower() == email_or_id.lower()):
                        student = dict(s)
                        break

            # Always run a password check to reduce timing/user-enumeration signals
            pwd_hash = student.get("passwordHash") or student.get("password") if student else None
            password_ok = verify_password(password, pwd_hash) if pwd_hash else verify_password(
                password, "pbkdf2_sha256$260000$0000000000000000$" + "0" * 64
            )

            if not student or not password_ok:
                rate_limit_hit(LOGIN_ATTEMPTS, client_ip, LOGIN_WINDOW_SECONDS)
                self._send_json({"error": "Invalid credentials. Please check your email/ID and password."}, 401)
                return

            # Upgrade legacy hashes to PBKDF2 on successful login
            if password_needs_rehash(pwd_hash):
                try:
                    new_hash = hash_password(password)
                    if HAS_MONGO and student.get("_id") is not None:
                        db.students.update_one({"_id": student["_id"]}, {"$set": {"passwordHash": new_hash}})
                    else:
                        student["passwordHash"] = new_hash
                except Exception as rehash_error:
                    print(f"[!] Password rehash notice: {rehash_error}", flush=True)

            rate_limit_clear(LOGIN_ATTEMPTS, client_ip)

            student_copy = dict(student)
            student_copy["id"] = str(student_copy.get("_id", student_copy.get("studentId", "")))
            if "passwordHash" in student_copy:
                del student_copy["passwordHash"]
            if "password" in student_copy:
                del student_copy["password"]
            if "_id" in student_copy:
                del student_copy["_id"]

            token = create_auth_token(student)
            print(f"[+] Successful login for PSG iTech student: {student_copy.get('name')} ({student_copy.get('email')})", flush=True)
            self._send_json({
                "token": token,
                "type": "Bearer",
                "student": student_copy,
                "message": "Login successful"
            })
            return

        # 5. POST /api/items (Add listing with Photo) - authenticated
        if path == "/api/items" or path == "/api/items/":
            auth = self._require_auth()
            if not auth:
                return

            item_id = f"item-{int(time.time() * 1000)}"
            owner_id = clean_text(auth.get("sub"), max_length=40)
            owner_name = clean_text(auth.get("email"), max_length=200)
            owner_dept = ""

            # Resolve the authenticated owner's display name/department server-side
            if HAS_MONGO:
                student_doc = db.students.find_one({"$or": [{"studentId": owner_id}, {"email": owner_id}]})
                if student_doc:
                    owner_name = clean_text(student_doc.get("name"), max_length=120, default=owner_name)
                    owner_dept = clean_text(student_doc.get("department"), max_length=120)
            else:
                for s in MEM_STUDENTS:
                    if s.get("studentId") == owner_id or s.get("email") == owner_id:
                        owner_name = clean_text(s.get("name"), max_length=120, default=owner_name)
                        owner_dept = clean_text(s.get("department"), max_length=120)
                        break
            if not owner_name:
                owner_name = "PSG iTech Student"
            if not owner_dept:
                owner_dept = "PSG iTech"

            title = clean_text(body.get("title"), max_length=160)
            if len(title) < 3:
                self._send_json({"error": "Item title must be at least 3 characters."}, 400)
                return
            description = clean_text(body.get("description"), max_length=2000)
            category = clean_text(body.get("category"), max_length=40, default="others").lower()
            if not re.match(r"^[a-z0-9_-]{1,40}$", category):
                category = "others"
            location = clean_text(body.get("location"), max_length=160, default="PSG iTech Campus")
            condition = clean_text(body.get("condition"), max_length=40, default="Like New")
            try:
                daily_price = float(body.get("dailyPrice", 50.0))
                deposit = float(body.get("securityDeposit", 200.0))
            except (TypeError, ValueError):
                self._send_json({"error": "Price and deposit must be valid numbers."}, 400)
                return
            if not (0 <= daily_price <= 100000) or not (0 <= deposit <= 1000000):
                self._send_json({"error": "Price or deposit is out of the allowed range."}, 400)
                return
            default_image = "https://lh3.googleusercontent.com/aida-public/AB6AXuB1HLeRSpdgX3LeoQ9mKLRt0X8SHRfjH-LLTBXn9iGVr2G2W-sbi6wLcDAmJHmAkp9a45-S86r-gBeooxf-ZHCzhnScTw_fb64wyFXHeYIB6Y2rhFj9Xwq8H3Jyo1MiRTL6sYNsNbbOLooGqLV8-tsClXqov9PCWGaswUaD8ATn6-PiMI7rw0UjAlEze1KZU8_A4u1qY4KyORJbuyQs7NNmzKB8rgmOz4INaa5dseI2"
            image_url = safe_http_url(body.get("imageUrl"), default=default_image)

            new_item = {
                "_id": item_id,
                "id": item_id,
                "title": title,
                "category": category,
                "categoryName": clean_text(body.get("categoryName"), max_length=60, default=category.capitalize()),
                "dailyPrice": daily_price,
                "securityDeposit": deposit,
                "condition": condition,
                "location": location,
                "campus": "PSG Institute of Technology and Applied Research",
                "ownerId": owner_id,
                "ownerName": owner_name,
                "ownerDept": owner_dept,
                "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
                "imageUrl": image_url,
                "rating": "5.0 ★ (New)",
                "description": description,
                "available": True,
                "createdAt": time.time()
            }

            if HAS_MONGO:
                db.items.insert_one(dict(new_item))
                if "_id" in new_item:
                    del new_item["_id"]
            else:
                MEM_ITEMS.insert(0, new_item)

            print(f"[+] Created new item: '{new_item['title']}' (ID: {item_id}) by {owner_name}", flush=True)
            self._send_json(new_item, 201)
            return

        # 6. POST /api/loans/{loan_id}/messages - agreed loan parties only
        if path.startswith("/api/loans/") and path.endswith("/messages"):
            loan_id = path[len("/api/loans/"):-len("/messages")].strip("/")
            auth = self._require_auth()
            if not auth:
                return
            loan_doc, role = self._authorize_agreed_loan_chat(auth, loan_id)
            if not loan_doc:
                return

            text = clean_text(body.get("text"), max_length=1000)
            if not text:
                self._send_json({"error": "Message text cannot be empty."}, 400)
                return

            sender_id = clean_text(auth.get("sub"), max_length=40)
            sender_doc = find_student_record(sender_id or auth.get("email"))
            sender_name = clean_text(
                (sender_doc.get("name") if sender_doc else None) or auth.get("email"),
                max_length=120,
                default="PSG iTech Student"
            )
            msg_id = f"msg-{int(time.time() * 1000)}-{secrets.token_hex(3)}"
            msg_doc = {
                "_id": msg_id,
                "id": msg_id,
                "loanId": str(loan_doc.get("_id", loan_doc.get("id", loan_id))),
                "senderId": sender_id,
                "senderEmail": clean_text(auth.get("email"), max_length=200),
                "senderName": sender_name,
                "senderRole": role,
                "text": text,
                "createdAt": time.time()
            }
            saved = append_loan_message(msg_doc["loanId"], msg_doc)
            self._send_json(saved, 201)
            return

        # 7. POST /api/loans/request - authenticated; pricing/owner come from the item record
        if path == "/api/loans/request":
            auth = self._require_auth()
            if not auth:
                return

            loan_id = f"loan-{int(time.time() * 1000)}"
            borrower_id = clean_text(auth.get("sub"), max_length=40)
            borrower_email = clean_text(auth.get("email"), max_length=200)
            borrower_doc = find_student_record(borrower_id or borrower_email)
            borrower_name = clean_text(borrower_doc.get("name") if borrower_doc else "", max_length=120, default="PSG iTech Student")
            borrower_dept = clean_text(borrower_doc.get("department") if borrower_doc else "", max_length=120, default="Student Peer")

            item_id = clean_text(body.get("itemId"), max_length=80)
            if not item_id:
                self._send_json({"error": "itemId is required."}, 400)
                return

            try:
                days = int(body.get("borrowDays", 3))
            except (TypeError, ValueError):
                self._send_json({"error": "borrowDays must be a number."}, 400)
                return
            if days < 1 or days > 365:
                self._send_json({"error": "Borrow duration must be between 1 and 365 days."}, 400)
                return

            # Resolve the item from the database / in-memory catalog. Never trust
            # client-supplied prices, owner identity, or titles.
            item_doc = None
            if HAS_MONGO:
                item_doc = db.items.find_one({"$or": [{"_id": item_id}, {"id": item_id}]})
            else:
                for it in MEM_ITEMS:
                    if it.get("id") == item_id or it.get("_id") == item_id:
                        item_doc = it
                        break

            if not item_doc:
                self._send_json({"error": "Item not found."}, 404)
                return

            lender_id = str(item_doc.get("ownerId", "")).strip()
            if lender_id and lender_id.lower() == borrower_id.lower():
                self._send_json({"error": "You cannot borrow your own listing."}, 400)
                return

            lender_doc = find_student_record(lender_id or item_doc.get("ownerEmail"))
            lender_email = clean_text((lender_doc.get("email") if lender_doc else None) or item_doc.get("ownerEmail"), max_length=200)

            try:
                daily_price = float(item_doc.get("dailyPrice", 0))
                deposit = float(item_doc.get("securityDeposit", 0))
            except (TypeError, ValueError):
                self._send_json({"error": "Item pricing is invalid."}, 500)
                return

            item_title = clean_text(item_doc.get("title"), max_length=160, default="Requested Item")
            item_image = safe_http_url(item_doc.get("imageUrl"), default="")
            lender_name = clean_text(item_doc.get("ownerName"), max_length=120, default="PSG iTech Classmate")
            lender_dept = clean_text(item_doc.get("ownerDept"), max_length=120, default="PSG iTech")
            location = clean_text(item_doc.get("location"), max_length=160, default="PSG iTech Campus")

            new_loan = {
                "_id": loan_id,
                "id": loan_id,
                "itemId": item_id,
                "itemTitle": item_title,
                "itemImage": item_image,
                "borrowerId": borrower_id,
                "borrowerName": borrower_name,
                "borrowerEmail": borrower_email,
                "borrowerDept": borrower_dept,
                "lenderId": lender_id,
                "lenderEmail": lender_email,
                "lenderName": lender_name,
                "lenderDept": lender_dept,
                "location": location,
                "borrowDays": days,
                "dailyPrice": daily_price,
                "totalFee": round(days * daily_price, 2),
                "securityDeposit": deposit,
                "status": "PENDING",
                "chatUnlocked": False,
                "createdAt": time.time()
            }

            if HAS_MONGO:
                db.loans.insert_one(dict(new_loan))
                if "_id" in new_loan:
                    del new_loan["_id"]
            else:
                with DATA_LOCK:
                    MEM_LOANS.append(new_loan)

            print(f"[+] Created loan request: {loan_id} for item '{item_title}' by {borrower_name} ({borrower_id})", flush=True)
            self._send_json(enrich_loan_for_viewer(new_loan, viewer_role="borrower"), 201)
            return

        self._send_json({"error": "Route not found"}, 404)

    # ================= PUT ENDPOINTS =================
    def do_PUT(self):
        try:
            self._handle_put()
        except RequestTooLarge:
            self._send_json({"error": "Request body is too large."}, 413)
        except Exception as e:
            print(f"[!] Unhandled error in PUT {self.path}: {e}", flush=True)
            self._send_json({"error": "Internal server error"}, 500)

    def _handle_put(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        body = self._read_json()

        # 1. Update Student Profile: PUT /api/students/{id} - authenticated, self only
        if path.startswith("/api/students/"):
            auth = self._require_auth()
            if not auth:
                return

            s_id = path.replace("/api/students/", "").strip()
            if not self._identity_matches(auth, s_id):
                self._send_json({"error": "You are not allowed to modify this profile."}, 403)
                return

            field_limits = {
                "name": 120,
                "dormLocation": 160,
                "dorm": 160,
                "department": 120,
                "yearOfStudy": 40,
                "phone": 30,
                "campus": 160,
            }
            update_data = {}
            for field, limit in field_limits.items():
                if field in body:
                    val = clean_text(body[field], max_length=limit)
                    if field == "dorm":
                        update_data["dormLocation"] = val
                    else:
                        update_data[field] = val

            if "phone" in update_data and not is_valid_phone(update_data["phone"]):
                self._send_json({"error": "Please provide a valid phone number."}, 400)
                return

            if not update_data:
                self._send_json({"error": "No valid update fields provided"}, 400)
                return

            updated_student = None
            if HAS_MONGO:
                db.students.update_one(
                    {
                        "$or": [
                            {"studentId": {"$regex": f"^{re.escape(s_id)}$", "$options": "i"}},
                            {"email": {"$regex": f"^{re.escape(s_id)}$", "$options": "i"}},
                            {"_id": s_id}
                        ]
                    },
                    {"$set": update_data}
                )
                updated_student = find_student_record(s_id)
            else:
                with DATA_LOCK:
                    for s in MEM_STUDENTS:
                        if s.get("studentId", "").lower() == s_id.lower() or s.get("email", "").lower() == s_id.lower():
                            s.update(update_data)
                            updated_student = find_student_record(s_id)
                            break

            if updated_student:
                print(f"[+] Successfully updated student profile for {s_id}", flush=True)
                self._send_json({
                    "success": True,
                    "student": updated_student,
                    "message": "Student profile updated successfully"
                })
                return
            else:
                self._send_json({"error": "Student account not found"}, 404)
                return

        if path.startswith("/api/loans/") and (path.endswith("/status") or path.endswith("/decision")):
            auth = self._require_auth()
            if not auth:
                return

            suffix = "/status" if path.endswith("/status") else "/decision"
            loan_id = path[len("/api/loans/"):-len(suffix)].strip("/")
            loan_doc = find_loan_record(loan_id)
            if not loan_doc:
                self._send_json({"error": "Loan not found."}, 404)
                return

            raw_status = body.get("status") or body.get("decision") or params.get("status", ["ACCEPTED"])[0]
            status_map = {
                "ACCEPT": "ACCEPTED",
                "ACCEPTED": "ACCEPTED",
                "AGREE": "ACCEPTED",
                "ACTIVE": "ACTIVE",
                "DECLINE": "DECLINED",
                "DECLINED": "DECLINED",
                "REJECT": "DECLINED",
                "RETURN": "RETURNED",
                "RETURNED": "RETURNED",
            }
            status_val = status_map.get(clean_text(raw_status, max_length=20).upper(), "")
            if not status_val:
                self._send_json({"error": "Unsupported loan status transition."}, 400)
                return

            role = self._loan_viewer_role(auth, loan_doc)
            if not role:
                self._send_json({"error": "You are not allowed to modify this loan."}, 403)
                return
            if status_val in ("ACCEPTED", "DECLINED", "ACTIVE") and role != "lender":
                self._send_json({"error": "Only the lender can accept or decline a borrow request."}, 403)
                return

            now_ts = time.time()
            fields_to_set = {"status": status_val, "updatedAt": now_ts}
            if status_val in AGREED_LOAN_STATUSES and not loan_doc.get("acceptedAt"):
                fields_to_set["acceptedAt"] = now_ts

            if HAS_MONGO:
                db.loans.update_one(
                    {"$or": [{"_id": loan_id}, {"id": loan_id}]},
                    {"$set": fields_to_set}
                )
            else:
                with DATA_LOCK:
                    for l in MEM_LOANS:
                        if l.get("id") == loan_id or l.get("_id") == loan_id:
                            l.update(fields_to_set)
                            break

            updated_doc = find_loan_record(loan_id) or {**loan_doc, **fields_to_set}
            enriched = enrich_loan_for_viewer(updated_doc, viewer_role=role)
            self._send_json({
                "success": True,
                "status": status_val,
                "loan": enriched,
                "updatedAt": now_ts
            })
            return

        self._send_json({"error": "Route not found"}, 404)

    # ================= DELETE ENDPOINTS =================
    def do_DELETE(self):
        try:
            self._handle_delete()
        except Exception as e:
            print(f"[!] Unhandled error in DELETE {self.path}: {e}", flush=True)
            self._send_json({"error": "Internal server error"}, 500)

    def _handle_delete(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/loans/"):
            auth = self._require_auth()
            if not auth:
                return

            loan_id = path.replace("/api/loans/", "").strip()
            loan_doc = find_loan_record(loan_id)
            if not loan_doc:
                self._send_json({"error": "Loan not found"}, 404)
                return

            if not self._loan_viewer_role(auth, loan_doc):
                self._send_json({"error": "You are not allowed to cancel this loan."}, 403)
                return

            if HAS_MONGO:
                db.loans.delete_one({"$or": [{"_id": loan_id}, {"id": loan_id}]})
                db.messages.delete_many({"loanId": str(loan_doc.get("_id", loan_doc.get("id", loan_id)))})
            else:
                global MEM_LOANS
                with DATA_LOCK:
                    MEM_LOANS = [l for l in MEM_LOANS if l.get("id") != loan_id and l.get("_id") != loan_id]
                    MEM_MESSAGES.pop(loan_id, None)
            print(f"[-] Deleted/Cancelled loan {loan_id}", flush=True)
            self._send_json({"success": True, "message": f"Loan {loan_id} deleted successfully"})
            return

        self._send_json({"error": "Route not found"}, 404)


def run_server(port=8080):
    server_address = ("", port)
    try:
        httpd = ThreadingHTTPServer(server_address, CampusLendAPIHandler)
        httpd.daemon_threads = True
    except OSError as e:
        if "10048" in str(e) or "Address already in use" in str(e):
            print(f"\n[!] Port {port} is already in use by another process.", flush=True)
            print(f"[!] If an existing server is running, stop it with Ctrl+C or run with a different port:\n    python api.py 8081\n", flush=True)
            sys.exit(1)
        raise
    print("=" * 65, flush=True)
    print(f"  PSG iTech Campus Lend API Server Running at:", flush=True)
    print(f"  --> http://localhost:{port}/", flush=True)
    print(f"  --> http://localhost:{port}/api/items", flush=True)
    print(f"  --> College Domain: @{COLLEGE_DOMAIN}", flush=True)
    db_name_display = os.environ.get("MONGO_DB_NAME", "lend")
    print(f"  --> MongoDB: {'Connected (' + db_name_display + ')' if HAS_MONGO else 'In-Memory Mode'}", flush=True)
    print("=" * 65, flush=True)
    print("Press Ctrl+C to stop the server.\n", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CampusLend API server.", flush=True)
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
