# The E-Library – Online Library Management System with AI-Based Book Recommendation

> **B.E. Computer Science & Engineering Capstone Project**  
> A complete, fully functional full-stack web application designed for academic libraries with intelligent, zero-cost AI book recommendations, book pricing in Indian Rupees (₹), and 14-day loan due-date tracking.

---

## 📖 1. Project Overview

**The E-Library** is a modern, responsive web application built to streamline university library operations and personalize student learning experiences. Unlike static library catalogs, The E-Library features a built-in **Content-Based AI Recommendation System** that automatically analyzes student interest profiles and borrow history to recommend relevant Computer Science and Engineering textbooks.

The application supports two distinct roles:
1. **Normal User / Student**: Register with areas of academic interest, search the live catalog, check real-time availability and prices in Indian Rupees (₹), borrow/request books, track 14-day due dates and overdue statuses, return books, and view personalized AI recommendations with explainable reasons.
2. **Library Administrator**: Access a protected control portal to monitor statistics (Total Books, Available Copies, Registered Users, Total Borrow Requests), add new books with custom prices, edit existing records and prices, remove inventory, review student accounts, and monitor loan circulation and returns.

---

## 💡 2. Key Features

### For Students / Users:
- **Hero & Landing Page**: Introduces the platform with real-time statistics, search box, and featured books with catalog prices.
- **Account Registration & Login**:
  - Secure registration capturing name, email, and selectable areas of interest (*Programming, Artificial Intelligence, Data Science, Cybersecurity, Networking, Web Development, Database, Cloud Computing, Computer Science*).
  - Secure password hashing using PBKDF2/SHA-256 via Werkzeug.
  - Session-based user authentication.
- **User Dashboard**:
  - Overview of currently available books and active loans.
  - Active overdue alert notification if any borrowed book has exceeded the 14-day return window.
  - Quick-search bar.
  - Top AI recommendations preview with match percentages and prices.
  - Recent requests list showing Issue Date, 14-Day Due Date, and quick return buttons.
- **Live Book Catalog & Search**:
  - Full-text search across Book Title, Author, Category, and Description directly in the database.
  - Category filter dropdown and quick filter pills.
  - Real-time book availability badges (**Available** / **Not Available**) and pricing in Indian Rupees (**₹**).
  - One-click **Request Book** functionality with instant transaction recording, automatic 14-day due date assignment, and catalog availability updates.
- **My Purchases / Requests**:
  - Track borrowed books with prices, Issue Date, Due Date, and loan status (**Active**, **Overdue**, **Returned**).
  - One-click **Return Book** action that automatically marks the loan as returned and restores availability in the catalog.
- **AI-Based Book Recommendations**:
  - Dedicated page displaying recommended books ranked by computed relevance score.
  - **Explainable AI (XAI)**: Explicit justification banners for each recommendation (e.g., *"Recommended because matches your registered interest in 'Artificial Intelligence', and you previously explored 'Artificial Intelligence: A Modern Approach'"*).
  - Book price display and direct borrow action from recommendation cards.

### For Library Administrators:
- **Dedicated Admin Login**:
  - Predefined credentials: `admin@elibrary.com` / `admin123`.
  - Protected by role-based session middleware (`@admin_required`).
- **Administrative Control Panel**:
  - Real-time metrics counters (Total Books, Available Copies, Registered Users, Total Requests).
  - **Add Book**: Form modal to add books with title, author, category, description, price (₹), and initial availability.
  - **Edit Book**: Form to modify catalog metadata, adjust prices, or toggle availability.
  - **Delete Book**: Secure deletion with client-side confirmation.
  - **Student Directory**: Inspect all registered students and their interest profiles.
  - **Circulation & Requests Log**: Monitor all borrowing records across all students with Issue Dates, 14-day Due Dates, Overdue indicators, and status update controls (*Active*, *Returned*, *Cancelled*).

---

## 🧠 3. AI-Based Recommendation System Architecture

### Content-Based Recommendation Approach
The recommendation system uses **Content-Based Filtering** implemented purely in Python without requiring paid cloud APIs (e.g., OpenAI, Google Cloud) or external subscriptions. It operates 100% locally with zero latency.

### How the Algorithm Computes Relevance:
1. **User Interest Vector (+12 points)**:
   Matches the book's discipline directly with the student's registered interests selected during signup. If a keyword appears in the title/summary, an additional +6 points is awarded.
2. **Borrowing History Affinity (+10 points)**:
   Analyzes books the student has previously requested or borrowed. If the target book shares a category with past borrowings, it receives +10 points (plus +2 per repeated interaction).
3. **Cross-Domain Curriculum Ontology (+5 points)**:
   Incorporates domain relationships specific to Computer Science Engineering:
   - *Programming* &harr; *Computer Science*, *Web Development*, *Data Structures*
   - *Artificial Intelligence* &harr; *Machine Learning*, *Data Science*, *Python*
   - *Cybersecurity* &harr; *Networking*, *Operating Systems*, *Cryptography*
   - *Database* &harr; *SQL & NoSQL*, *Cloud Computing*, *Web Development*
4. **Lexical Keyword Co-occurrence (+3 points per token)**:
   Extracts significant tokens from book titles and descriptions to score textual similarity with past reading material.
5. **Availability Bonus (+2 points)**:
   Available books receive a slight boost to ensure actionable recommendations.
6. **Dynamic Reason Generator**:
   Synthesizes a human-readable sentence explaining exactly *why* the book was suggested, providing transparent, explainable recommendations.

---

## 🛠️ 4. Technology Stack

| Layer | Technologies Used | Description |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Font Awesome 6 | Clean, responsive academic UI optimized for desktop and mobile |
| **Backend** | Python 3.12, Flask 3.1, Werkzeug | RESTful routing, session management, template rendering, and validation |
| **Database** | SQLite3 (`database.db`) | Relational storage with foreign keys and automatic initialization |
| **Recommendation** | Pure Python (`recommendation.py`) | Content-based scoring and explainable rationale engine |
| **Security** | Werkzeug Security (`generate_password_hash`, `check_password_hash`) | Industry-standard password hashing, session guards, input validation |

---

## 🗄️ 5. Database Schema

The SQLite database (`database.db`) includes three relational tables:

```sql
-- 1. Students / Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,          -- Hashed with Werkzeug PBKDF2/SHA-256
    interests TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Books Catalog Table (with Prices in INR)
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    available INTEGER NOT NULL DEFAULT 1,
    price REAL NOT NULL DEFAULT 450.00, -- Book price in Indian Rupees (₹)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Purchases & Borrow Requests Table (with Issue and Due Dates)
CREATE TABLE requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Book Issue Date
    due_date TIMESTAMP,                               -- Default 14 days after issue
    return_date TIMESTAMP,                            -- Populated upon book return
    status TEXT NOT NULL DEFAULT 'Active',            -- 'Active', 'Returned', 'Cancelled'
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
);
```

---

## 🎓 6. College Faculty Backend & Database Demonstration Guide

When presenting this project to your college faculty or examination committee, follow this straightforward demonstration sequence:

### Step 1: Start the Backend Server
Show that the project runs a real Python Flask server locally:
```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\E-Library"
python app.py
```
*Point out to the faculty that Flask starts on `http://127.0.0.1:5000` and automatically connects to the SQLite database `database.db`.*

### Step 2: Live Database Inspection via Terminal (`inspect_db.py`)
Run the built-in database inspection utility in a separate terminal:
```powershell
python inspect_db.py
```
This utility provides an immediate, professional inspection report showing:
1. **Database Path & Size**: Proves `database.db` is an actual SQLite file on disk.
2. **Table Schemas**: Shows `users`, `books` (with `price`), and `requests` (with `request_date`, `due_date`, and `return_date`).
3. **Live Prices**: Shows actual values stored in the database in Indian Rupees (e.g. ₹499.00, ₹699.00, ₹799.00).
4. **Circulation Tracking**: Shows 14-day due dates calculated dynamically (`Issue Date + 14 days`).
5. **Security & Privacy**: Proves that passwords are never stored in plain text and password hashes are redacted from public display.

### Step 3: Route Mapping Table for Viva Questions
If your faculty asks *"Where is this feature handled in the code?"*, refer to this direct mapping:

| Faculty Question / Feature | Flask Route in `app.py` | Database Query / Operation | Template Rendered |
|---|---|---|---|
| **Book Search** | `@app.route('/books')` | `SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR category LIKE ?` | `books.html` |
| **Book Pricing** | `@app.route('/books')`, `@app.route('/admin/books/add')` | `INSERT INTO books (..., price) VALUES (...)` | `books.html`, `admin_dashboard.html` |
| **Issue Date & Due Date** | `@app.route('/request-book/<int:book_id>')` | Calculates `now + timedelta(days=14)`, `INSERT INTO requests (..., due_date)` | Redirects to `/my-requests` |
| **Overdue Detection** | `enrich_request()` in `app.py` | Compares `datetime.now() > due_date` | Displays `<span class="badge bg-danger">Overdue</span>` |
| **Return Book & Restore Stock** | `@app.route('/return-book/<int:request_id>')` | `UPDATE requests SET status='Returned'`, `UPDATE books SET available=1` | `purchases.html` |
| **AI Recommendation** | `@app.route('/recommendations')` | Calls `get_recommendations()` in `recommendation.py` | `recommendations.html` |
| **User Authentication** | `@app.route('/register')`, `@app.route('/login')` | `check_password_hash(user['password'], password)` | `login.html`, `register.html` |
| **Admin Route Protection** | `@admin_required` decorator | Checks `session.get('is_admin') == True` | `admin_dashboard.html` |

---

## 🚀 7. Installation & How to Run

### System Requirements:
- Operating System: Windows 10/11, macOS, or Linux
- Python: Version 3.10 or higher
- Web Browser: Google Chrome, Mozilla Firefox, Microsoft Edge, or Safari

### Option A: One-Click Desktop Launcher
Double-click **`Launch_ELibrary.bat`** on your Desktop. It will launch the application and automatically open `http://127.0.0.1:5000` in your default browser.

### Option B: Terminal Commands
```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\E-Library"
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in any web browser.

---

## 🔑 8. Default Credentials for Evaluation

### Administrator Account:
- **URL**: `http://127.0.0.1:5000/admin/login`
- **Email**: `admin@elibrary.com`
- **Password**: `admin123`
*(Note: A one-click "Auto-fill" button is provided on the login page for quick examiner evaluation).*

### Pre-seeded Demo Student Account:
- **URL**: `http://127.0.0.1:5000/login`
- **Email**: `student@elibrary.com`
- **Password**: `student123`
- **Registered Interests**: *Programming, Artificial Intelligence*

---

## 🧪 9. Automated Test Suite

A complete test suite (`test_project.py`) is included to verify all functionality:
```powershell
python test_project.py
```
**Test Results (12/12 PASS)**:
- `test_01_database_and_sample_books`: Verified sample books inserted.
- `test_02_home_page`: Verified hero section and UI elements.
- `test_03_registration_and_password_hashing`: Verified password hashing security.
- `test_04_duplicate_registration_rejected`: Verified validation on duplicate email.
- `test_05_student_login_and_logout`: Verified authentication and session lifecycle.
- `test_06_catalog_search`: Verified live database querying.
- `test_07_book_request_and_return_cycle`: Verified inventory decrement and return restoral.
- `test_08_ai_recommendation_algorithm`: Verified content-based relevance and reason synthesis.
- `test_09_admin_authentication_and_dashboard`: Verified access controls and metrics.
- `test_10_admin_book_crud_with_price`: Verified Add, Edit with Price (₹), and Delete book workflows.
- `test_11_book_prices_in_database_and_catalog`: Verified Indian Rupee prices across all catalog items.
- `test_12_due_date_calculation_and_overdue_logic`: Verified 14-day due date calculation and overdue detection.

---

## 🔮 10. Future Enhancements

- **Automatic Fine Calculation**: Imposing ₹5/day penalty on overdue loans past the 14-day mark.
- **QR Code / Barcode Scanning**: Integration for quick student ID and physical book scanning.
- **Collaborative Filtering**: Incorporating student star-rating matrices alongside content-based filtering.
- **E-Book Reader Integration**: Allowing direct online reading of open-access PDF textbooks.

---

## 🌐 11. Step-by-Step Free Deployment on PythonAnywhere

You can deploy this application completely free on **PythonAnywhere** (no credit card required). Follow these straightforward steps:

### Step 1: Create a Free PythonAnywhere Account
1. Visit [https://www.pythonanywhere.com/](https://www.pythonanywhere.com/) and register for a free **"Beginner"** account.
2. Your live website URL will be: `https://<your-username>.pythonanywhere.com`.

### Step 2: Upload Project Files to PythonAnywhere
Open a **Bash Console** from your PythonAnywhere Dashboard and clone your project repository:
```bash
git clone https://github.com/<your-username>/E-Library.git
```
*(Alternatively, zip your `E-Library` project folder, upload the zip file via the **Files** tab on PythonAnywhere, and extract it using `unzip E-Library.zip`).*

### Step 3: Install Required Dependencies
In the PythonAnywhere **Bash Console**, run:
```bash
cd ~/E-Library
pip install --user -r requirements.txt
```
*(All required libraries: `Flask`, `Werkzeug`, `requests` will be installed to your PythonAnywhere environment).*

### Step 4: Configure the Web App
1. Navigate to the **Web** tab on PythonAnywhere.
2. Click **"Add a new web app"**.
3. Your domain will default to `<your-username>.pythonanywhere.com`. Click **Next**.
4. In the framework selection dialog, choose **"Manual configuration"** (Do *not* choose "Flask", as manual configuration gives you clean control over WSGI and modern Python versions).
5. Select **Python 3.10**, **Python 3.11**, or **Python 3.12**.

### Step 5: Configure the WSGI Configuration File
1. In the **Web** tab under the **Code** section, click on the **WSGI configuration file** link (e.g. `/var/www/<your-username>_pythonanywhere_com_wsgi.py`).
2. Delete all existing sample code in that editor and paste the contents from [`wsgi_pythonanywhere.py`](file:///c:/E-Library/wsgi_pythonanywhere.py):
   ```python
   import sys
   import os

   # Replace 'your-username' with your actual PythonAnywhere username:
   username = 'your-username'
   project_home = f'/home/{username}/E-Library'

   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   # Ensure current working directory is project root
   try:
       os.chdir(project_home)
   except Exception:
       pass

   # Import Flask application object
   from app import app as application
   ```
3. Click the **Save** button in the upper right.

### Step 6: Configure Static Files (High-Performance CSS/JS Serving)
In the **Web** tab, scroll down to the **Static files** section and add a mapping:
- **URL**: `/static/`
- **Directory**: `/home/<your-username>/E-Library/static`

### Step 7: Reload & Test the Live Application
1. Scroll to the top of the **Web** tab and click the large green button **"Reload <your-username>.pythonanywhere.com"**.
2. Open your live site in a browser: `https://<your-username>.pythonanywhere.com`
3. Test logging in:
   - **Student Login**: `student@elibrary.com` / `student123`
   - **Admin Login**: `admin@elibrary.com` / `admin123`
4. Verify catalog search, 14-day book requests, prices in ₹, returns, and AI recommendations live!

