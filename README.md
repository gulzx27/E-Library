# E-Library — Online Library Management System

A responsive web-based library management system built using Python, Flask, SQLite, HTML, CSS, and JavaScript. The application helps students discover books, manage borrowing requests, and receive personalized book recommendations based on their interests.

**Live Demo:** [https://e-library-app.onrender.com/](https://e-library-app.onrender.com/)

## Project Overview

E-Library is a full-stack web application designed to simplify library operations for students and administrators. It provides a searchable book catalog, student accounts, book borrowing and returns, administrative book management, and a content-based recommendation system.

## Features

### Student Features

- Student registration and login.
- Personalized dashboard.
- Browse and search the book catalog.
- Filter books by category.
- View book details, availability, and prices.
- Request available books and track borrowing status.
- View issue dates and 14-day due dates.
- Return borrowed books.
- Receive book recommendations based on interests and borrowing activity.

### Administrator Features

- Dedicated admin login.
- Dashboard with library statistics.
- Add, edit, and delete books.
- Manage book details, categories, descriptions, prices, and availability.
- View registered students.
- Monitor borrowing requests and returns.

### Recommendation System

The project includes a content-based recommendation system implemented in Python. It uses information such as student interests, book categories, titles, descriptions, and borrowing activity to calculate relevance scores and provide recommendations.

The recommendation engine runs locally within the Python application and does not require a paid AI API.

## Demo Student Login

Use these demo credentials to explore the student features of the application.

- **Email:** `student@elibrary.com`
- **Password:** `student123`

**Note:** These credentials are intended for project demonstration and evaluation. If they do not work on the live deployment, register a new student account through the application.

For security, administrator credentials are not published in this README.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python 3.12, Flask |
| Database | SQLite3 |
| Recommendation Engine | Python |
| Authentication | Flask sessions and Werkzeug password hashing |
| Deployment | Render |
| Version Control | Git and GitHub |

## Project Structure

```text
E-Library/
├── app.py
├── database.py
├── recommendation.py
├── inspect_db.py
├── test_project.py
├── requirements.txt
├── README.md
├── .gitignore
├── wsgi_pythonanywhere.py
├── database.db
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   ├── manifest.json
│   └── service-worker.js
└── templates/
    ├── index.html
    ├── base.html
    ├── books.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── purchases.html
    ├── recommendations.html
    ├── admin_login.html
    ├── admin_dashboard.html
    ├── admin_edit_book.html
    ├── 404.html
    └── 500.html
```

*Note: `database.db` is used for local database operations and is excluded from the Git repository.*

## Requirements

- Python 3.12 recommended.
- Git.
- Visual Studio Code or another code editor.
- A modern web browser.

## Run the Project Locally

### 1. Clone the Repository

```bash
git clone https://github.com/gulzx27/E-Library.git
cd E-Library
```

### 2. Create a Virtual Environment

**Windows PowerShell:**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS or Linux:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the Application

```bash
python app.py
```

Open the following address in your browser:

[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

The application uses SQLite for local database operations. Its initialization code creates the required tables and inserts sample books when the database is empty.

## Database Design

The application uses SQLite with three primary tables.

### Users

Stores student account information, password hashes, interests, and account creation dates.

### Books

Stores book titles, authors, categories, descriptions, availability, prices, and creation dates.

### Requests

Stores student borrowing requests, book references, request dates, due dates, return dates, and borrowing statuses.

Foreign-key relationships connect borrowing records to students and books.

## Live Deployment

The application is deployed using Render.

**Live URL:** [https://e-library-app.onrender.com/](https://e-library-app.onrender.com/)

The current deployment uses the following settings:

- **Runtime:** Python
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- **Database:** SQLite

### Database Limitation

The current Render free-service setup uses temporary filesystem storage. SQLite data created on the hosted instance may be lost after restarts, redeployments, or other instance changes.

This configuration is suitable for a demonstration where persistent records are not required. A persistent database or storage configuration is recommended if the application is used for ongoing library operations.

## Testing

The project includes `test_project.py`, which contains automated tests for core application behavior.

Run the tests locally with:

```bash
python test_project.py
```

Review the test output to confirm which tests pass in your current environment.

## Future Enhancements

- Persistent hosted database.
- Book barcode or QR-code scanning.
- Fine calculation for overdue books.
- Book ratings and collaborative recommendations.
- Online reading for supported digital books.
- Improved reporting and analytics.

## Project Purpose

This project demonstrates full-stack web development, relational database management, authentication, CRUD operations, and content-based recommendation techniques in an academic library application.

---

**E-Library — Making library management simpler and book discovery more personalized.**