# LendLoop - Campus Peer-to-Peer Web Application

A full-featured, responsive desktop & tablet web application for peer-to-peer campus borrowing & lending, built with modern HTML, Tailwind CSS tokens, and JavaScript.

Featuring the official **LendLoop** branding and vector logo assets, this web application converts the design tokens and concepts from `stitch_campuslend_mobile_app` into a modern marketplace web experience.

---

## 🚀 How to Open & Run

Open [`index.html`](file:///d:/lend/index.html) in your browser:
- Double click [`index.html`](file:///d:/lend/index.html) or right-click and choose **Open with Browser** (Chrome, Edge, Firefox, Safari).
- Or run any lightweight static server:
  ```bash
  python -m http.server 8080
  # or
  npx serve .
  ```

---

## 💻 Web App Architecture & Features

The interface is built as a complete desktop-first web application:

### 1. **Authentication Gateway Page (Login & Registration)**
- **Gated Access**: When opening [`index.html`](file:///d:/lend/index.html), the user is greeted by the **Login / Registration Gateway** *before entering* the marketplace.
- **Photos & Assets from `stitch_campuslend_mobile_app`**:
  - **Login Visual Card**: Features the 3D college study photo (`AB6AXuAEz5MC...`) from `campuslend_login`, "4,800+ Students Active" badge, "98% Trust Rating", and verified student testimonials.
  - **Registration Visual Card**: Features the university study group photo (`AB6AXuDJE71q...`) from `campuslend_registration`, "Verified Student Network" badge, and "Campus Community" social proof banner.
- **Interactive Dual-Tab Gateway**:
  - **Log In Tab**:
    - Pre-filled `.edu` verified campus email field (`alex.chen@stanford.edu`).
    - Password field with show/hide toggle.
    - "Remember me on this campus device" checkbox.
    - **"Log In to LendLoop"** primary button — unlocks and transitions into the marketplace web application.
    - Multi-color **Google Student SSO** button with official brand iconography.
    - University 2FA security badge and 256-bit SSL indicator.
  - **Register Tab**:
    - Complete 7-field student registration form from `campuslend_registration`: Legal Name, Student ID ("For in-person handshakes"), College Email, Department/Major dropdown, Year of Study pills (Freshman, Soph, Junior, Senior, Grad), Password with 4-bar strength indicator ("Strong (8+ chars, symbol)"), and Confirm Password with match verification.
    - **"Create Student Account"** button — registers the student, updates session profile, and transitions into the web app.
    - **Quick Demo Access** button in top header for instant 1-click evaluation.
  - **Sign Out Flow**:
    - Users can sign out at any time from the top navigation profile dropdown or profile view to safely return to the Login Gateway.

### 2. **Global Desktop Header Navigation**
- **Brand Logo & Wordmark**: Features the new vector LendLoop infinity loop logo mark + dual-tone typography (`assets/logo.svg`).
- **Campus Selector**: Switch between university hubs (Stanford, UC Berkeley, MIT, Harvard).
- **Global Instant Search**: Search bar with real-time keyword matching across titles, descriptions, and lenders.
- **Top Navigation**: Instant switching between **Marketplace**, **My Loans**, and **How It Works**.
- **Header Actions**:
  - `+ Post an Item` prominent primary CTA.
  - Interactive Notifications flyout with due reminders and request alerts.
  - User profile menu with quick links and sign out.

### 2. **Marketplace Catalog View (`view-marketplace`)**
- **Campus Hero Banner**: Highlighting verified student networks, trust score, and average term savings.
- **Category Chips**: Fast filtering by Textbooks, Tech & Electronics, Calculators & Lab Gear, Sports & Outdoor, and Dorm Living.
- **Desktop Two-Column Workspace**:
  - **Left Filter Sidebar**: Availability toggle ("Available Immediately"), daily rate price range slider, campus hall/dorm selector (Wilbur, Stern, Green Library, Tressider, Gates), and escrow safety badge.
  - **Right Main Grid**: 3-column responsive card catalog with high-res product photos, price tags, favorite heart button, lender avatar, condition badge, and click-to-view navigation.
  - **Sort Dropdown**: Sort by Featured, Price (Low to High / High to Low), or Top Lender Rating.
  - **Empty Search State**: Friendly reset prompt when no items match the filter criteria.

### 3. **Desktop Product Detail View (`view-item-detail`)**
- **Two-Column Split Layout**:
  - **Left Column (7 cols)**: 16:10 high-resolution hero gallery, status badges, condition pill, attributes summary (Refundable Deposit, Max 14 Days, Lender Rating), item specifications, and verified peer lender profile card with chat button.
  - **Right Column (5 cols - Sticky)**: Rental duration selector (+/- days) with dynamic price calculation, optional message to lender, price breakdown table (daily rate × days + deposit), and **Request to Borrow** CTA.

### 4. **Desktop Loans Dashboard (`view-my-loans`)**
- **Metric Cards**: Active Borrowing, Items Out on Loan, Pending Requests, and Completed Loans.
- **Segmented Control Tabs**:
  - **Borrowing**: Active borrowings with due date countdowns, overdue warnings, and **Return Item** action.
  - **Lending**: Items lent out with active earnings counter ($42.00) and borrower information.
  - **Incoming Requests**: Student requests with one-click **Accept Handover** or **Decline**.
- **Interactive QR Code Return Handover Modal**:
  - Generates SVG QR code and secure verification token (`LL-STAN-9842`) to simulate in-person deposit release.

### 5. **Student Profile & Settings (`view-profile`)**
- 2-Column desktop layout:
  - Left: Student verification badge, department, dorm room, karma score, and quick edit profile button.
  - Right: **My Listed Items** management with active item cards, edit button, and delete action.
  - University Single Sign-On (SSO) security badge.

### 6. **Listing Creation Modal**
- Accessible anytime from the top navigation bar.
- Form fields: Item title, category, condition, daily price ($/day), security deposit ($), campus pickup hall, and description.
- Automatically prepends new listings into the marketplace and user profile.

### 7. **Footer**
- Complete desktop footer with category shortcuts, trust & safety guarantees, active campus hubs, and copyright.

---

## 🎨 Design System

- **Collegiate Navy Primary**: `#002753`
- **Electric Blue**: `#0051d5` / `#316bf3`
- **LendLoop Emerald**: `#16a34a` / `#14532d`
- **Clean White & Surface Layers**: `#ffffff`, `#f8faff`, `#f1f4fd`, `#e8edff`
- **Typography**: Google Fonts *Plus Jakarta Sans* (headlines, pricing) and *Inter* (body, labels)
- **Icons**: Google *Material Symbols Outlined*
