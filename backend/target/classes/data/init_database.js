/**
 * CampusLend / LendLoop - MongoDB Database Initialization & Seed Script
 * 
 * Usage:
 *   mongosh mongodb://localhost:27017/campuslend_db init_database.js
 * Or copy and paste the contents into MongoDB Compass / mongosh terminal.
 */

// 1. Switch to or create database
db = db.getSiblingDB("campuslend_db");

print("=================================================");
print(" Initializing CampusLend Database: campuslend_db ");
print("=================================================");

// 2. Drop existing collections to start fresh (optional, safe for re-runs)
db.students.drop();
db.items.drop();
db.loans.drop();
db.notifications.drop();

// 3. Create Collections & Indexes
print("-> Creating collections and indexes...");

db.createCollection("students");
db.students.createIndex({ "email": 1 }, { unique: true });
db.students.createIndex({ "studentId": 1 }, { unique: true });

db.createCollection("items");
db.items.createIndex({ "category": 1 });
db.items.createIndex({ "available": 1 });
db.items.createIndex({ "ownerId": 1 });

db.createCollection("loans");
db.loans.createIndex({ "borrowerId": 1 });
db.loans.createIndex({ "lenderId": 1 });
db.loans.createIndex({ "itemId": 1 });
db.loans.createIndex({ "status": 1 });

db.createCollection("notifications");
db.notifications.createIndex({ "studentId": 1 });
db.notifications.createIndex({ "createdAt": -1 });

// 4. Seed Demo Students
print("-> Seeding students collection...");
db.students.insertMany([
  {
    "_id": "SU-9824102",
    "studentId": "SU-9824102",
    "name": "Alex J. Chen",
    "email": "alex.chen@stanford.edu",
    // BCrypt hash for "Stanford2026!"
    "passwordHash": "$2a$10$7R9rG.s8fP75p5y6XpA7.O3u2dCg5M2Kk4Kj8L1Mn9OpQrStUvWxY",
    "department": "Computer Science & Engineering",
    "yearOfStudy": "Junior",
    "dormLocation": "Wilbur Hall 304",
    "campus": "Stanford University",
    "role": "STUDENT",
    "trustScore": 98,
    "activeLoansCount": 2,
    "createdAt": new Date()
  },
  {
    "_id": "SU-7731904",
    "studentId": "SU-7731904",
    "name": "Sarah Lin",
    "email": "sarah.lin@stanford.edu",
    "passwordHash": "$2a$10$7R9rG.s8fP75p5y6XpA7.O3u2dCg5M2Kk4Kj8L1Mn9OpQrStUvWxY",
    "department": "Applied Mathematics",
    "yearOfStudy": "Sophomore",
    "dormLocation": "Wilbur Hall 112",
    "campus": "Stanford University",
    "role": "STUDENT",
    "trustScore": 99,
    "activeLoansCount": 1,
    "createdAt": new Date()
  },
  {
    "_id": "SU-ADMIN-01",
    "studentId": "SU-ADMIN-01",
    "name": "Campus Moderator",
    "email": "admin@stanford.edu",
    "passwordHash": "$2a$10$7R9rG.s8fP75p5y6XpA7.O3u2dCg5M2Kk4Kj8L1Mn9OpQrStUvWxY",
    "department": "Campus Operations",
    "yearOfStudy": "Staff",
    "dormLocation": "Tressider Center 201",
    "campus": "Stanford University",
    "role": "ADMIN",
    "trustScore": 100,
    "activeLoansCount": 0,
    "createdAt": new Date()
  }
]);

// 5. Seed Catalog Items
print("-> Seeding items collection...");
db.items.insertMany([
  {
    "_id": "item-1",
    "title": "TI-84 Plus CE Graphing Calculator",
    "category": "stationery",
    "categoryName": "Calculators & Lab",
    "dailyPrice": 3.50,
    "securityDeposit": 20.00,
    "condition": "Like New",
    "location": "Wilbur Hall • 0.2 mi",
    "campus": "Stanford Campus",
    "ownerId": "SU-7731904",
    "ownerName": "Sarah Lin",
    "ownerDept": "Sophomore • Applied Mathematics",
    "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuBM8VSzPWz6gX7VI2wzCYRejzZ-cxNpuaEF-mrtYyc4P20zvX2frfHkS75qBmQ7sNSciIYrMNM5VK1ZMyXi3W8ShFLb7o-zZNhhGqJAdNUbM3Z-b77r5tSXgdPIB6dd4mzmgFolQkHmrepl88pZ7AKd6OFrAyTCVunaRI3SuyVpfaalf0FqpiFIZkBil0Rq-_pMRvPb1lpO70yIbtS2D1m0a7Z9-EWNDqXSpV3R7YzR",
    "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuCwzEoEAOySUGjNOHtVUJfX4kzk2JoXBWr8O_2W6OlPBOBEyzFpdkwPF9maQ9UpdNsMNhfCUS2r3co300xpXSH1WgDkybFb8GNzCGFQuiKrPsYr-hmZl5O8hYxVk-y9cXuGdkTrUC89_-faqEUSw6bHHB1b3BkIkLNRObwI4vphIge7osJfNg6G1RmPKoEmOoxAuMrEH7yfzjBIMWa_DCjAE0B1vTF0hLqb6MycvIIR",
    "rating": "4.9 ★ (18 loans)",
    "description": "Pristine Python Edition color graphing calculator with backlit display and rechargeable battery. Essential for Math 51, CS 109, Chem 31, and all midterms or finals. Sanitized and fully charged.",
    "available": true,
    "createdAt": new Date()
  },
  {
    "_id": "item-2",
    "title": "Campbell Biology 12th Edition Hardcover",
    "category": "books",
    "categoryName": "Textbooks",
    "dailyPrice": 2.00,
    "securityDeposit": 15.00,
    "condition": "Pristine",
    "location": "Stern Hall • 0.4 mi",
    "campus": "Stanford Campus",
    "ownerId": "SU-9824102",
    "ownerName": "Marcus T.",
    "ownerDept": "Pre-Med • Bio Dept",
    "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
    "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHzF2ArCYVDUbZmI5k-3Auz7nNqDBA4WqGQ1_r8IIU8jjqDVNVlooZAqi6nibGOpGadYKu5ScBbKKgWnsr9ydHbAltNtedVgEgaBaLKfU3mkvw3s76vF3PLWIMxVCHi2JEtw-gzEwPkPdyYeDOy4DPmUnWHKUK0VL90C9XVINWLVarO1OgZfW830QxaJX5WPLTzllZIizBk3oRRULosxsviytiqWvpYwa3i9q7yI-j",
    "rating": "4.8 ★ (12 loans)",
    "description": "Clean hardcover edition without tears or missing pages. Has high-yield margin notes for Bio 81 and Bio 82. Great for semester reviews.",
    "available": true,
    "createdAt": new Date()
  },
  {
    "_id": "item-3",
    "title": "Sony WH-1000XM4 Noise Cancelling",
    "category": "tech",
    "categoryName": "Tech & Electronics",
    "dailyPrice": 4.00,
    "securityDeposit": 30.00,
    "condition": "Excellent",
    "location": "Green Library • 0.1 mi",
    "campus": "Stanford Campus",
    "ownerId": "SU-9824102",
    "ownerName": "Elena R.",
    "ownerDept": "Engineering • Senior",
    "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuDPK1wGgvcZzVIu09lEX1h_MzqjkCm43D_4Gld-fUyrR9IOfggN9H8l2cyKaQMsay2y4vJ_DLobml1FlJd0Ala2y1FLIQdTzFyYBHhYNvgc9JS5svtcYjYuHmxH000cZoAk7B2YX9tpxlpUfQjdI0l-7qkb2jzCotbZSLOEbmhCufoSzHFGW-2d8lPok-lStjxEb0oy5NWMdVzckaT0O6ERhshe9ub0pDFa3hvavx5J",
    "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuBkiquaYFgXakbP2mClmnfb7Va95cC2ekw5VVdqNTX6jzILz4X_lJKi8F7grlVAE-D9QiYeYNyjJfBNCInzQNdNbTdhKGLlWQxRmNdrhjptxFxbyvnmSlNKt4noiBYmHuVR9dyRrTDmvqLd6x9ViR5S6d4p7abPPi0nVk1HllDhaVaucdQJVULxFyeoPQ-MIcFK2c62h2EK7TIpoWfeB3YsuX_Kqfn_xkqORUID6qZG",
    "rating": "5.0 ★ (26 loans)",
    "description": "Active noise cancellation over-ear headphones. Unrivaled for deep focus in Green Library or noisy dormitory lounges. 30-hour battery life.",
    "available": true,
    "createdAt": new Date()
  },
  {
    "_id": "item-4",
    "title": "Heavy Duty Kryptonite U-Lock with Cable",
    "category": "sports",
    "categoryName": "Sports & Outdoor",
    "dailyPrice": 1.50,
    "securityDeposit": 10.00,
    "condition": "Sturdy",
    "location": "Tressider Quad • 0.3 mi",
    "campus": "Stanford Campus",
    "ownerId": "SU-9824102",
    "ownerName": "David K.",
    "ownerDept": "Economics • Junior",
    "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
    "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuD8LJ5er6DzREDNtgIhPowV_RLu0QJ7E6WBjDYlDPkdDFUGYbzCXQAQv_5mxifD6texvT-FrKICtTvmQPgroK95DNV0jUrDaWNxDd1l-3csq3mAfU02tGPToGD5bh2P1lSXX_gF5WvYXB2pghXiBoURCAhoQSxeyhMiSl8mPumqbg16PpeRys7ZfhVcdEAALS07xemOog2RtG5rnYGZ1_D_opGEsZdWgn7fzbV_BbD3",
    "rating": "4.9 ★ (14 loans)",
    "description": "Hardened steel bicycle lock with 4ft looped steel cable. Includes 2 keys. Essential for keeping bikes and e-scooters protected on campus.",
    "available": true,
    "createdAt": new Date()
  },
  {
    "_id": "item-5",
    "title": "Java Software Solutions (8th Ed)",
    "category": "books",
    "categoryName": "Textbooks",
    "dailyPrice": 2.00,
    "securityDeposit": 15.00,
    "condition": "Like New",
    "location": "Gates CS Building • 0.2 mi",
    "campus": "Stanford Campus",
    "ownerId": "SU-9824102",
    "ownerName": "Kevin M.",
    "ownerDept": "CS • Junior",
    "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuDPK1wGgvcZzVIu09lEX1h_MzqjkCm43D_4Gld-fUyrR9IOfggN9H8l2cyKaQMsay2y4vJ_DLobml1FlJd0Ala2y1FLIQdTzFyYBHhYNvgc9JS5svtcYjYuHmxH000cZoAk7B2YX9tpxlpUfQjdI0l-7qkb2jzCotbZSLOEbmhCufoSzHFGW-2d8lPok-lStjxEb0oy5NWMdVzckaT0O6ERhshe9ub0pDFa3hvavx5J",
    "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuDM-3UvkaYlTm0DmafG2spCGujBwntxSSe3OWHJz2R8uZKO50r7sHrasD3L-RWNH5rIg8TcLJD2yYvO4w8Abv0xkONRIw6-ue9a5vRe7wg2Zt8vo1anc-i4vu_mL-m7Tfd8tYeYSzOnTUdi2JqAxO67ILac5J9NFvaF0b6rMr6D2wQUv_sCTRorNe4KdsJtEdMqwUsvQHfiCUTDcJlkq0kCviYFnDezQVCzX1cNNSRq",
    "rating": "4.7 ★ (9 loans)",
    "description": "Foundations of program design, object-oriented concepts, recursion, and data structures. Recommended for CS 106A/B coursework and midterms.",
    "available": true,
    "createdAt": new Date()
  },
  {
    "_id": "item-6",
    "title": "Logitech MX Master 3S Wireless Mouse",
    "category": "tech",
    "categoryName": "Tech & Electronics",
    "dailyPrice": 2.50,
    "securityDeposit": 25.00,
    "condition": "Pristine",
    "location": "Design Loft • 0.3 mi",
    "campus": "Stanford Campus",
    "ownerId": "SU-9824102",
    "ownerName": "Jordan T.",
    "ownerDept": "Product Design",
    "ownerAvatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
    "imageUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuD7gwQjV590U9vx14Fk3gWAVGNeM94g7uvPbrLTk2sSK8gny8hVVMT7_0_gm89wFpynlso1Q9OX3izu6Wd4PNJLwwEJNRNjDD2aJQl_5o0aKz5Q1ma_k-mNZwBS7eSiO6fd43lyYEJQMNYJTyVboZBYo00lgRiaz0tR2Zw_aomqYqDQpCp93tw6nEGJjG_rCBVbXdJ1kTE1eCchh_pJHvktAPkVxwhBPFeAVLkhixo7",
    "rating": "4.9 ★ (19 loans)",
    "description": "Ergonomic quiet click mouse with electromagnetic MagSpeed scroll wheel. Perfect for design studios, CAD, Figma, or programming.",
    "available": true,
    "createdAt": new Date()
  }
]);

// 6. Seed Sample Loans
print("-> Seeding loans collection...");
db.loans.insertMany([
  {
    "_id": "loan-101",
    "itemId": "item-1",
    "borrowerId": "SU-9824102",
    "lenderId": "SU-7731904",
    "borrowDays": 3,
    "totalFee": 10.50,
    "securityDeposit": 20.00,
    "status": "ACCEPTED",
    "startDate": new Date(Date.now() - 86400000), // Yesterday
    "dueDate": new Date(Date.now() + 2 * 86400000), // 2 days from now
    "createdAt": new Date(Date.now() - 86400000)
  },
  {
    "_id": "loan-102",
    "itemId": "item-3",
    "borrowerId": "SU-7731904",
    "lenderId": "SU-9824102",
    "borrowDays": 2,
    "totalFee": 8.00,
    "securityDeposit": 30.00,
    "status": "PENDING",
    "startDate": new Date(),
    "dueDate": new Date(Date.now() + 2 * 86400000),
    "createdAt": new Date()
  }
]);

// 7. Seed Sample Notifications
print("-> Seeding notifications collection...");
db.notifications.insertMany([
  {
    "_id": "notif-01",
    "studentId": "SU-9824102",
    "title": "Borrow Request Accepted",
    "message": "Sarah Lin accepted your request for the TI-84 Plus CE Graphing Calculator.",
    "type": "SUCCESS",
    "read": false,
    "createdAt": new Date(Date.now() - 3600000)
  },
  {
    "_id": "notif-02",
    "studentId": "SU-9824102",
    "title": "Return Reminder",
    "message": "TI-84 Plus CE is due in 48 hours at Wilbur Hall.",
    "type": "INFO",
    "read": false,
    "createdAt": new Date()
  }
]);

print("=================================================");
print("✅ CampusLend Database Seed Completed Successfully!");
print("   - Students: " + db.students.countDocuments());
print("   - Items:    " + db.items.countDocuments());
print("   - Loans:    " + db.loans.countDocuments());
print("   - Notifs:   " + db.notifications.countDocuments());
print("=================================================");

