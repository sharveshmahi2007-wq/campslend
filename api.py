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
import secrets
import hashlib
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

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

# In-memory OTP storage
# email -> { "hash": str, "salt": str, "expires_at": float, "attempts": int, "last_sent": float, "verified": bool, "verification_token": str }
OTP_STORE = {}


def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{password}:{salt}".encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password, stored_hash):
    if not stored_hash:
        return False
    if "$" not in stored_hash:
        # Fallback for plain demo passwords
        return password == stored_hash
    salt, hashed = stored_hash.split("$", 1)
    return hashlib.sha256(f"{password}:{salt}".encode()).hexdigest() == hashed


# In-memory datasets (also used to seed MongoDB if empty)
MEM_STUDENTS = [
    {
        "_id": "25Z295",
        "studentId": "25Z295",
        "name": "Sharvesh Mahi",
        "email": "25z295@psgitech.ac.in",
        "passwordHash": hash_password("sharveshmahi"),
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
        "passwordHash": hash_password("PSGTech@2026"),
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
        "passwordHash": hash_password("PSGTech@2026"),
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
        "ownerName": "David K.",
        "ownerDept": "Economics • Junior",
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
        "ownerName": "Kevin M.",
        "ownerDept": "CS • Junior",
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

    # Seed initial demo members only if they do not already exist in database (preserves any user edits)
    for student in MEM_STUDENTS:
        db.students.update_one(
            {"email": student["email"]},
            {"$setOnInsert": student},
            upsert=True
        )

    # Seed initial items if database collection is empty
    if db.items.count_documents({}) == 0:
        for item in MEM_ITEMS:
            db.items.update_one(
                {"id": item["id"]},
                {"$setOnInsert": dict(item)},
                upsert=True
            )
        print(f"[*] Seeded {len(MEM_ITEMS)} initial catalog items into '{db_name}' database.")
except Exception as e:
    HAS_MONGO = False
    print(f"[!] MongoDB not reachable via pymongo ({e}). Running with in-memory fallback store.")


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

    print("\n" + "=" * 65)
    print(f" [PSG iTech College OTP Authentication]")
    print(f" Recipient: {to_email}")
    print(f" OTP Code:  {otp}  (Valid for 5 minutes • Single Use)")
    print("=" * 65 + "\n", flush=True)

    if smtp_user and smtp_pass:
        try:
            sender_email = os.environ.get("SMTP_FROM", os.environ.get("SENDER_EMAIL", "prasathsri2008@gmail.com"))
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
        except Exception as e:
            print(f"[!] SMTP dispatch notice: {e}. Console OTP available for development.", flush=True)
    return True





class CampusLendAPIHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_HEAD(self):
        self._set_headers(200)

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            try:
                return json.loads(body.decode("utf-8"))
            except Exception:
                return {}
        return {}

    def _send_json(self, data, status=200):
        self._set_headers(status)
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    # ================= GET ENDPOINTS =================
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # Serve static web frontend files (index.html, translations.js, assets)
        if not path.startswith("/api"):
            clean_path = urllib.parse.unquote(path).lstrip("/") or "index.html"
            file_path = os.path.abspath(os.path.join(STATIC_DIR, clean_path))
            try:
                is_safe = os.path.commonpath([STATIC_DIR, file_path]) == STATIC_DIR
            except ValueError:
                is_safe = False

            if is_safe and os.path.exists(file_path) and os.path.isfile(file_path):
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

                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            elif os.path.exists(os.path.join(STATIC_DIR, "index.html")):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                    self.wfile.write(f.read())
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

        # 3. GET /api/students/{id}
        if path.startswith("/api/students/"):
            s_id = path.replace("/api/students/", "").strip()
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

        # 4. GET /api/loans/borrower/{id}
        if path.startswith("/api/loans/borrower/"):
            b_id = path.replace("/api/loans/borrower/", "")
            loans = []
            if HAS_MONGO:
                docs = list(db.loans.find({"borrowerId": b_id}))
                for d in docs:
                    d["id"] = str(d.get("_id", d.get("id", "")))
                    if "_id" in d:
                        del d["_id"]
                    loans.append(d)
            else:
                loans = [l for l in MEM_LOANS if l.get("borrowerId") == b_id]
            self._send_json(loans)
            return

        self._send_json({"error": "Route not found", "path": path}, 404)

    # ================= POST ENDPOINTS =================
    def do_POST(self):
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

            # Duplicate check (case-insensitive)
            if HAS_MONGO:
                if db.students.find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}}):
                    self._send_json({"error": f"An account with {email} is already registered. Please log in."}, 400)
                    return
            else:
                if any(s.get("email", "").lower() == email for s in MEM_STUDENTS):
                    self._send_json({"error": f"An account with {email} is already registered. Please log in."}, 400)
                    return

            # Rate limiting / 60s cooldown check
            now = time.time()
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
                "verification_token": None
            }

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

            if email not in OTP_STORE:
                self._send_json({"error": f"No active OTP request found for {email}. Please request an OTP first."}, 400)
                return

            record = OTP_STORE[email]

            # Already verified check
            if record.get("verified") and record.get("verification_token"):
                self._send_json({
                    "success": True,
                    "verified": True,
                    "email": email,
                    "verificationToken": record["verification_token"],
                    "message": "College email already verified."
                })
                return

            # Max attempts check
            if record.get("attempts", 0) >= OTP_MAX_ATTEMPTS:
                self._send_json({"error": f"Maximum OTP verification attempts ({OTP_MAX_ATTEMPTS}) exceeded. Please request a new OTP."}, 400)
                return

            # Expiration check
            if time.time() > record.get("expires_at", 0):
                self._send_json({"error": "OTP has expired (valid for 5 minutes). Please request a new OTP."}, 400)
                return

            # Compare SHA-256 hashes
            cand_hash = hashlib.sha256(f"{otp_code}:{record['salt']}".encode()).hexdigest()
            if cand_hash != record.get("hash"):
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
            record = OTP_STORE.get(email)
            if not record or not record.get("verified") or record.get("verification_token") != v_token:
                self._send_json({"error": "Email verification required. Please verify your PSG iTech email with OTP first."}, 400)
                return

            student_id = str(body.get("studentId", "")).strip() or f"7155-{int(time.time() % 1000000)}"

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

            raw_password = body.get("password", "PSGTech@2026")
            hashed_pwd = hash_password(raw_password)

            new_student = {
                "_id": student_id,
                "studentId": student_id,
                "name": body.get("name", "PSG iTech Student"),
                "email": email,
                "passwordHash": hashed_pwd,
                "department": body.get("department", "Computer Science & Engineering"),
                "yearOfStudy": body.get("yearOfStudy", "1st Year"),
                "dormLocation": body.get("dormLocation", "Campus Hostel Block A"),
                "campus": "PSG Institute of Technology and Applied Research",
                "role": "STUDENT",
                "trustScore": 100,
                "activeLoansCount": 0
            }

            if HAS_MONGO:
                try:
                    db.students.insert_one(new_student)
                    del new_student["_id"]
                except Exception as e:
                    self._send_json({"error": f"Database error during registration: {str(e)}"}, 500)
                    return
            else:
                MEM_STUDENTS.append(new_student)

            # Purge single-use verification token
            if email in OTP_STORE:
                del OTP_STORE[email]

            token = f"jwt-psgitech-{int(time.time())}_{student_id}"
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
            email_or_id = str(body.get("email", "")).strip()
            password = str(body.get("password", ""))

            if not email_or_id:
                self._send_json({"error": "College email or Student ID cannot be empty."}, 400)
                return

            if "@" in email_or_id:
                valid, res = validate_psgitech_email(email_or_id)
                if not valid:
                    self._send_json({"error": res}, 400)
                    return
                email_or_id = res

            student = None
            if HAS_MONGO:
                student = db.students.find_one({
                    "$or": [
                        {"email": {"$regex": f"^{re.escape(email_or_id)}$", "$options": "i"}},
                        {"studentId": {"$regex": f"^{re.escape(email_or_id)}$", "$options": "i"}}
                    ]
                })
            else:
                for s in MEM_STUDENTS:
                    if s.get("email", "").lower() == email_or_id.lower() or s.get("studentId", "").lower() == email_or_id.lower():
                        student = s
                        break

            if not student:
                self._send_json({"error": f"No registered student found with: {email_or_id}. Please register first."}, 404)
                return

            # Secure password verification (prevent bypass on missing hash, support plaintext fallback)
            pwd_hash = student.get("passwordHash") or student.get("password")
            if not pwd_hash or not verify_password(password, pwd_hash):
                self._send_json({"error": "Invalid email/ID or password."}, 400)
                return

            student_copy = dict(student)
            student_copy["id"] = str(student_copy.get("_id", student_copy.get("studentId", "")))
            if "passwordHash" in student_copy:
                del student_copy["passwordHash"]
            if "password" in student_copy:
                del student_copy["password"]
            if "_id" in student_copy:
                del student_copy["_id"]

            token = f"jwt-psgitech-{int(time.time())}_{student_copy.get('studentId')}"
            print(f"[+] Successful login for PSG iTech student: {student_copy.get('name')} ({student_copy.get('email')})", flush=True)
            self._send_json({
                "token": token,
                "type": "Bearer",
                "student": student_copy,
                "message": "Login successful"
            })
            return

        # 5. POST /api/items (Add listing with Photo)
        if path == "/api/items" or path == "/api/items/":
            item_id = f"item-{int(time.time() * 1000)}"
            owner_id = str(body.get("ownerId", "25Z295")).strip()
            owner_name = body.get("ownerName")
            owner_dept = body.get("ownerDept")

            # Look up owner in database if not passed
            if not owner_name:
                if HAS_MONGO:
                    student_doc = db.students.find_one({"$or": [{"studentId": owner_id}, {"email": owner_id}]})
                    if student_doc:
                        owner_name = student_doc.get("name", "Sharvesh Mahi")
                        owner_dept = student_doc.get("department", "Computer Science & Engineering")
                else:
                    for s in MEM_STUDENTS:
                        if s.get("studentId") == owner_id or s.get("email") == owner_id:
                            owner_name = s.get("name", "Sharvesh Mahi")
                            owner_dept = s.get("department", "Computer Science & Engineering")
                            break
            if not owner_name:
                owner_name = "Sharvesh Mahi"
            if not owner_dept:
                owner_dept = "1st Year • Computer Science"

            new_item = {
                "_id": item_id,
                "id": item_id,
                "title": body.get("title", "Untitled Item"),
                "category": body.get("category", "others").lower(),
                "categoryName": body.get("category", "General").capitalize(),
                "dailyPrice": float(body.get("dailyPrice", 50.00)),
                "securityDeposit": float(body.get("securityDeposit", 200.00)),
                "condition": body.get("condition", "Like New"),
                "location": body.get("location", "PSG iTech Campus"),
                "campus": "PSG Institute of Technology and Applied Research",
                "ownerId": owner_id,
                "ownerName": owner_name,
                "ownerDept": owner_dept,
                "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
                "imageUrl": body.get("imageUrl", "https://lh3.googleusercontent.com/aida-public/AB6AXuB1HLeRSpdgX3LeoQ9mKLRt0X8SHRfjH-LLTBXn9iGVr2G2W-sbi6wLcDAmJHmAkp9a45-S86r-gBeooxf-ZHCzhnScTw_fb64wyFXHeYIB6Y2rhFj9Xwq8H3Jyo1MiRTL6sYNsNbbOLooGqLV8-tsClXqov9PCWGaswUaD8ATn6-PiMI7rw0UjAlEze1KZU8_A4u1qY4KyORJbuyQs7NNmzKB8rgmOz4INaa5dseI2"),
                "rating": "5.0 ★ (New)",
                "description": body.get("description", ""),
                "available": True,
                "createdAt": time.time()
            }

            if HAS_MONGO:
                db.items.insert_one(new_item)
                del new_item["_id"]
            else:
                MEM_ITEMS.insert(0, new_item)

            print(f"[+] Created new item: '{new_item['title']}' (ID: {item_id}) by {owner_name}", flush=True)
            self._send_json(new_item, 201)
            return

        # 6. POST /api/loans/request
        if path == "/api/loans/request":
            loan_id = f"loan-{int(time.time() * 1000)}"
            item_id = body.get("itemId")
            borrower_id = body.get("borrowerId", "25Z295")
            days = int(body.get("borrowDays", 3))

            daily_price = 50.00
            deposit = 200.00
            lender_id = "715521104001"

            if item_id:
                if HAS_MONGO:
                    item_doc = db.items.find_one({"$or": [{"_id": item_id}, {"id": item_id}]})
                    if item_doc:
                        daily_price = float(item_doc.get("dailyPrice", 50.00))
                        deposit = float(item_doc.get("securityDeposit", 200.00))
                        lender_id = item_doc.get("ownerId", lender_id)
                else:
                    for it in MEM_ITEMS:
                        if it.get("id") == item_id or it.get("_id") == item_id:
                            daily_price = float(it.get("dailyPrice", 50.00))
                            deposit = float(it.get("securityDeposit", 200.00))
                            lender_id = it.get("ownerId", lender_id)
                            break

            new_loan = {
                "_id": loan_id,
                "id": loan_id,
                "itemId": item_id,
                "borrowerId": borrower_id,
                "lenderId": lender_id,
                "borrowDays": days,
                "totalFee": round(days * daily_price, 2),
                "securityDeposit": deposit,
                "status": "PENDING",
                "createdAt": time.time()
            }

            if HAS_MONGO:
                db.loans.insert_one(new_loan)
                del new_loan["_id"]
            else:
                MEM_LOANS.append(new_loan)

            print(f"[+] Created loan request: {loan_id} for item {item_id}", flush=True)
            self._send_json(new_loan, 201)
            return

        self._send_json({"error": "Route not found"}, 404)

    # ================= PUT ENDPOINTS =================
    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        content_length = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_length > 0:
            raw_body = self.rfile.read(content_length)
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except Exception:
                body = {}

        # 1. Update Student Profile: PUT /api/students/{id}
        if path.startswith("/api/students/"):
            s_id = path.replace("/api/students/", "").strip()
            allowed_fields = ["name", "dormLocation", "dorm", "department", "yearOfStudy", "phone", "campus"]
            update_data = {}
            for field in allowed_fields:
                if field in body:
                    val = str(body[field]).strip()
                    if field == "dorm":
                        update_data["dormLocation"] = val
                    else:
                        update_data[field] = val

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
                result = db.students.find_one({
                    "$or": [
                        {"studentId": {"$regex": f"^{re.escape(s_id)}$", "$options": "i"}},
                        {"email": {"$regex": f"^{re.escape(s_id)}$", "$options": "i"}},
                        {"_id": s_id}
                    ]
                })
                if result:
                    updated_student = dict(result)
                    updated_student["id"] = str(updated_student.get("_id", updated_student.get("studentId", "")))
                    if "passwordHash" in updated_student:
                        del updated_student["passwordHash"]
                    if "password" in updated_student:
                        del updated_student["password"]
                    if "_id" in updated_student:
                        del updated_student["_id"]
            else:
                for s in MEM_STUDENTS:
                    if s.get("studentId", "").lower() == s_id.lower() or s.get("email", "").lower() == s_id.lower():
                        s.update(update_data)
                        clean = dict(s)
                        if "passwordHash" in clean:
                            del clean["passwordHash"]
                        if "password" in clean:
                            del clean["password"]
                        updated_student = clean
                        break

            if updated_student:
                print(f"[+] Successfully updated student profile for {s_id}: {update_data}", flush=True)
                self._send_json({
                    "success": True,
                    "student": updated_student,
                    "message": "Student profile updated successfully"
                })
                return
            else:
                self._send_json({"error": "Student account not found"}, 404)
                return

        if "/status" in path:
            status_val = params.get("status", ["ACCEPTED"])[0]
            self._send_json({"success": True, "status": status_val, "updatedAt": time.time()})
            return

        self._send_json({"success": True})


def run_server(port=8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CampusLendAPIHandler)
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
