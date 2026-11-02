#!/usr/bin/env python3
"""
CampusLend / LendLoop - Python REST API Server & Connector
Connects the web frontend to MongoDB (campuslend_db) at http://localhost:8080/api

To run:
    python api.py
    (or: python api.py --port 8080)
"""

import sys
import os
import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

# Try importing pymongo; fallback to in-memory store if not installed
try:
    from pymongo import MongoClient
    mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    # Test connection
    mongo_client.server_info()
    db = mongo_client["campuslend_db"]
    HAS_MONGO = True
    print("[*] Successfully connected to MongoDB at localhost:27017 (campuslend_db)")
except Exception as e:
    HAS_MONGO = False
    print(f"[!] MongoDB not reachable via pymongo ({e}). Running with in-memory fallback store.")

# In-memory fallback dataset (matching MongoDB seed)
MEM_ITEMS = [
    {
        "_id": "item-1",
        "id": "item-1",
        "title": "TI-84 Plus CE Graphing Calculator",
        "category": "stationery",
        "categoryName": "Calculators & Lab",
        "dailyPrice": 3.50,
        "securityDeposit": 20.00,
        "condition": "Like New",
        "location": "Wilbur Hall • 0.2 mi",
        "campus": "Stanford Campus",
        "ownerName": "Sarah Lin",
        "ownerDept": "Sophomore • Applied Mathematics",
        "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuBM8VSzPWz6gX7VI2wzCYRejzZ-cxNpuaEF-mrtYyc4P20zvX2frfHkS75qBmQ7sNSciIYrMNM5VK1ZMyXi3W8ShFLb7o-zZNhhGqJAdNUbM3Z-b77r5tSXgdPIB6dd4mzmgFolQkHmrepl88pZ7AKd6OFrAyTCVunaRI3SuyVpfaalf0FqpiFIZkBil0Rq-_pMRvPb1lpO70yIbtS2D1m0a7Z9-EWNDqXSpV3R7YzR",
        "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuCwzEoEAOySUGjNOHtVUJfX4kzk2JoXBWr8O_2W6OlPBOBEyzFpdkwPF9maQ9UpdNsMNhfCUS2r3co300xpXSH1WgDkybFb8GNzCGFQuiKrPsYr-hmZl5O8hYxVk-y9cXuGdkTrUC89_-faqEUSw6bHHB1b3BkIkLNRObwI4vphIge7osJfNg6G1RmPKoEmOoxAuMrEH7yfzjBIMWa_DCjAE0B1vTF0hLqb6MycvIIR",
        "rating": "4.9 ★ (18 loans)",
        "description": "Pristine Python Edition color graphing calculator with backlit display and rechargeable battery.",
        "available": True
    },
    {
        "_id": "item-2",
        "id": "item-2",
        "title": "Campbell Biology 12th Edition Hardcover",
        "category": "books",
        "categoryName": "Textbooks",
        "dailyPrice": 2.00,
        "securityDeposit": 15.00,
        "condition": "Pristine",
        "location": "Stern Hall • 0.4 mi",
        "campus": "Stanford Campus",
        "ownerName": "Marcus T.",
        "ownerDept": "Pre-Med • Bio Dept",
        "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
        "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHzF2ArCYVDUbZmI5k-3Auz7nNqDBA4WqGQ1_r8IIU8jjqDVNVlooZAqi6nibGOpGadYKu5ScBbKKgWnsr9ydHbAltNtedVgEgaBaLKfU3mkvw3s76vF3PLWIMxVCHi2JEtw-gzEwPkPdyYeDOy4DPmUnWHKUK0VL90C9XVINWLVarO1OgZfW830QxaJX5WPLTzllZIizBk3oRRULosxsviytiqWvpYwa3i9q7yI-j",
        "rating": "4.8 ★ (12 loans)",
        "description": "Clean hardcover edition without tears or missing pages. Has high-yield margin notes.",
        "available": True
    }
]

MEM_LOANS = []
MEM_STUDENTS = [
    {
        "studentId": "SU-9824102",
        "name": "Alex J. Chen",
        "email": "alex.chen@stanford.edu",
        "department": "Computer Science & Engineering",
        "yearOfStudy": "Junior",
        "dormLocation": "Wilbur Hall 304"
    }
]


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
            return json.loads(body.decode("utf-8"))
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
            rel_path = path.lstrip("/") or "index.html"
            file_path = os.path.join(STATIC_DIR, rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
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

            # Filter by search if provided
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
            s_id = path.replace("/api/students/", "")
            if HAS_MONGO:
                student = db.students.find_one({"studentId": s_id}) or db.students.find_one({"_id": s_id})
                if student:
                    student["id"] = str(student.get("_id", student.get("studentId", "")))
                    if "passwordHash" in student:
                        del student["passwordHash"]
                    if "_id" in student:
                        del student["_id"]
                    self._send_json(student)
                    return
            else:
                for s in MEM_STUDENTS:
                    if s.get("studentId") == s_id:
                        self._send_json(s)
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

        # 5. Default 404
        self._send_json({"error": "Route not found", "path": path}, 404)

    # ================= POST ENDPOINTS =================
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json()

        # 1. POST /api/items (Add listing with Photo)
        if path == "/api/items" or path == "/api/items/":
            item_id = f"item-{int(time.time() * 1000)}"
            new_item = {
                "_id": item_id,
                "id": item_id,
                "title": body.get("title", "Untitled Item"),
                "category": body.get("category", "others").lower(),
                "categoryName": body.get("category", "General").capitalize(),
                "dailyPrice": float(body.get("dailyPrice", 3.00)),
                "securityDeposit": float(body.get("securityDeposit", 20.00)),
                "condition": body.get("condition", "Like New"),
                "location": body.get("location", "Wilbur Hall"),
                "campus": "Stanford Campus",
                "ownerId": body.get("ownerId", "SU-9824102"),
                "ownerName": "Alex Rivera",
                "ownerDept": "Junior • Computer Science",
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

            print(f"[+] Created new item: '{new_item['title']}' (ID: {item_id})")
            self._send_json(new_item, 201)
            return

        # 2. POST /api/auth/login
        if path == "/api/auth/login":
            email = body.get("email", "").strip().lower()
            student = None
            if HAS_MONGO:
                student = db.students.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
                if student:
                    student["id"] = str(student.get("_id", student.get("studentId", "")))
                    if "passwordHash" in student:
                        del student["passwordHash"]
                    if "_id" in student:
                        del student["_id"]
            else:
                for s in MEM_STUDENTS:
                    if s.get("email", "").lower() == email:
                        student = s
                        break

            if not student:
                # Default guest / demo student
                student = {
                    "studentId": "SU-9824102",
                    "name": "Alex J. Chen",
                    "email": email or "alex.chen@stanford.edu",
                    "department": "Computer Science & Engineering",
                    "yearOfStudy": "Junior",
                    "dormLocation": "Wilbur Hall 304"
                }

            token = f"token_{int(time.time())}_{student.get('studentId')}"
            self._send_json({
                "token": token,
                "type": "Bearer",
                "student": student,
                "message": "Login successful"
            })
            return

        # 3. POST /api/auth/register
        if path == "/api/auth/register":
            student_id = body.get("studentId", f"SU-{int(time.time() % 10000000)}")
            new_student = {
                "_id": student_id,
                "studentId": student_id,
                "name": body.get("name", "Student Peer"),
                "email": body.get("email", "student@stanford.edu"),
                "department": body.get("department", "General Studies"),
                "yearOfStudy": body.get("yearOfStudy", "Freshman"),
                "dormLocation": body.get("dormLocation", "Campus Dorm"),
                "campus": "Stanford University",
                "role": "STUDENT",
                "trustScore": 100,
                "activeLoansCount": 0
            }

            if HAS_MONGO:
                try:
                    db.students.insert_one(new_student)
                    del new_student["_id"]
                except Exception as e:
                    pass
            else:
                MEM_STUDENTS.append(new_student)

            token = f"token_{int(time.time())}_{student_id}"
            self._send_json({
                "token": token,
                "type": "Bearer",
                "student": new_student,
                "message": "Student account registered successfully"
            }, 201)
            return

        # 4. POST /api/loans/request
        if path == "/api/loans/request":
            loan_id = f"loan-{int(time.time() * 1000)}"
            item_id = body.get("itemId")
            borrower_id = body.get("borrowerId", "SU-9824102")
            days = int(body.get("borrowDays", 3))

            new_loan = {
                "_id": loan_id,
                "id": loan_id,
                "itemId": item_id,
                "borrowerId": borrower_id,
                "lenderId": "SU-7731904",
                "borrowDays": days,
                "totalFee": days * 3.50,
                "securityDeposit": 20.00,
                "status": "PENDING",
                "createdAt": time.time()
            }

            if HAS_MONGO:
                db.loans.insert_one(new_loan)
                del new_loan["_id"]
            else:
                MEM_LOANS.append(new_loan)

            print(f"[+] Created loan request: {loan_id} for item {item_id}")
            self._send_json(new_loan, 201)
            return

        self._send_json({"error": "Route not found"}, 404)

    # ================= PUT ENDPOINTS =================
    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # PUT /api/loans/{id}/status?status=ACCEPTED
        if "/status" in path:
            status_val = params.get("status", ["ACCEPTED"])[0]
            self._send_json({"success": True, "status": status_val, "updatedAt": time.time()})
            return

        self._send_json({"success": True})


def run_server(port=8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CampusLendAPIHandler)
    print("=" * 60)
    print(f"  CampusLend Python API Server Running at:")
    print(f"  --> http://localhost:{port}/api/items")
    print(f"  --> MongoDB: {'Connected (campuslend_db)' if HAS_MONGO else 'In-Memory Mode'}")
    print("=" * 60)
    print("Press Ctrl+C to stop the server.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CampusLend API server.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)

