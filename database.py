"""
Database Module for E-Library Management System
Handles SQLite database connection, table initialization, migration, and seeding sample data.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Reliable project-relative path to SQLite database (works locally and on PythonAnywhere)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('ELIBRARY_DB_PATH', os.path.join(BASE_DIR, 'database.db'))


def get_db_connection():
    """Establish and return a SQLite database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database tables, apply migrations safely, and seed sample data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            interests TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Create Books Table with price field in Indian Rupees (₹)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            available INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL DEFAULT 450.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Create Purchases/Requests Table with issue_date, due_date, and return_date
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            return_date TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'Active',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
        )
    ''')

    # --- Safe Migrations for Existing Databases ---
    # Migration A: Ensure 'price' column exists in 'books' table
    cursor.execute("PRAGMA table_info(books)")
    book_columns = [row['name'] for row in cursor.fetchall()]
    if 'price' not in book_columns:
        cursor.execute("ALTER TABLE books ADD COLUMN price REAL NOT NULL DEFAULT 450.00")

    # Migration B: Ensure 'due_date' and 'return_date' columns exist in 'requests' table
    cursor.execute("PRAGMA table_info(requests)")
    req_columns = [row['name'] for row in cursor.fetchall()]
    if 'due_date' not in req_columns:
        cursor.execute("ALTER TABLE requests ADD COLUMN due_date TIMESTAMP")
    if 'return_date' not in req_columns:
        cursor.execute("ALTER TABLE requests ADD COLUMN return_date TIMESTAMP")

    # Update any existing requests that lack a due_date (default to 14 days after request_date)
    cursor.execute("SELECT id, request_date FROM requests WHERE due_date IS NULL")
    requests_to_update = cursor.fetchall()
    for req in requests_to_update:
        r_date_str = req['request_date']
        try:
            clean_date = r_date_str.split('.')[0]
            dt = datetime.strptime(clean_date, '%Y-%m-%d %H:%M:%S')
        except Exception:
            dt = datetime.now()
        due_dt = dt + timedelta(days=14)
        cursor.execute("UPDATE requests SET due_date = ? WHERE id = ?", (due_dt.strftime('%Y-%m-%d %H:%M:%S'), req['id']))

    # Check if sample books already exist
    cursor.execute("SELECT COUNT(*) AS count FROM books")
    book_count = cursor.fetchone()['count']

    sample_books_data = [
        (
            "Python Programming",
            "John Zelle",
            "Programming",
            "An introductory and comprehensive guide to Python syntax, data structures, object-oriented concepts, and practical coding exercises.",
            1,
            499.00
        ),
        (
            "Java Programming",
            "Herbert Schildt",
            "Programming",
            "In-depth guide covering Java syntax, OOP design patterns, multithreading, collections framework, and robust backend engineering.",
            1,
            550.00
        ),
        (
            "Data Structures and Algorithms",
            "Thomas H. Cormen",
            "Computer Science",
            "The definitive textbook on algorithmic complexity, trees, graphs, sorting, searching, and dynamic programming.",
            1,
            699.00
        ),
        (
            "Database Management Systems",
            "Raghu Ramakrishnan",
            "Database",
            "Core fundamentals of relational databases, SQL queries, relational algebra, normal forms, indexing, and ACID transactions.",
            1,
            520.00
        ),
        (
            "Computer Networks",
            "Andrew S. Tanenbaum",
            "Networking",
            "Comprehensive study of network layers, OSI and TCP/IP protocol suites, routing, congestion control, and wireless networks.",
            1,
            580.00
        ),
        (
            "Artificial Intelligence: A Modern Approach",
            "Stuart Russell & Peter Norvig",
            "Artificial Intelligence",
            "The leading textbook in AI covering intelligent agents, state search, knowledge representation, inference, and machine learning.",
            1,
            799.00
        ),
        (
            "Machine Learning Basics",
            "Ian Goodfellow & Yoshua Bengio",
            "Artificial Intelligence",
            "A foundational guide to supervised learning, gradient descent, loss functions, deep neural networks, and regularization.",
            1,
            640.00
        ),
        (
            "Web Development with Modern Technologies",
            "Jon Duckett",
            "Web Development",
            "Complete modern guide covering HTML5 semantic layout, responsive CSS3 styling, modern JavaScript, DOM manipulation, and REST APIs.",
            1,
            450.00
        ),
        (
            "Cybersecurity Fundamentals",
            "William Stallings",
            "Cybersecurity",
            "Essential guide to information security principles, encryption standards, authentication mechanisms, network firewalls, and defenses.",
            1,
            530.00
        ),
        (
            "Cloud Computing Essentials",
            "Thomas Erl",
            "Cloud Computing",
            "Concepts of cloud service models (IaaS, PaaS, SaaS), virtualization, cloud architecture, elasticity, and AWS/Azure deployment.",
            1,
            480.00
        ),
        (
            "Data Science from Scratch",
            "Joel Grus",
            "Data Science",
            "Practical guide to data cleaning, probability, statistics, linear algebra, and data modeling using Python libraries.",
            1,
            560.00
        ),
        (
            "Operating System Concepts",
            "Abraham Silberschatz",
            "Computer Science",
            "Comprehensive coverage of processes, threads, CPU scheduling, synchronization, deadlocks, and virtual memory.",
            1,
            620.00
        ),
        (
            "Full Stack JavaScript with React & Node",
            "Ethan Brown",
            "Web Development",
            "Hands-on guide to building reactive single-page applications, Express backend servers, and MongoDB/SQL database integration.",
            1,
            490.00
        ),
        (
            "Network Security and Cryptography",
            "Behrouz A. Forouzan",
            "Cybersecurity",
            "Detailed mathematical and practical exploration of symmetric/asymmetric encryption, RSA, digital signatures, and SSL/TLS.",
            1,
            540.00
        ),
        (
            "SQL and NoSQL Database Architecture",
            "Pramod J. Sadalage",
            "Database",
            "Comparative analysis of relational tables vs document stores, key-value caches, graph databases, and polyglot persistence.",
            1,
            510.00
        )
    ]

    if book_count == 0:
        cursor.executemany('''
            INSERT INTO books (title, author, category, description, available, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_books_data)
    else:
        # Update existing books with realistic individual prices if they are currently set to default or 0
        for b_item in sample_books_data:
            cursor.execute('''
                UPDATE books SET price = ? WHERE title = ? AND (price IS NULL OR price = 450.0 OR price = 0)
            ''', (b_item[5], b_item[0]))

    # Check if a sample demo user exists for immediate evaluation
    cursor.execute("SELECT COUNT(*) AS count FROM users")
    user_count = cursor.fetchone()['count']
    if user_count == 0:
        demo_user = (
            "Alex Mercer",
            "student@elibrary.com",
            generate_password_hash("student123"),
            "Programming, Artificial Intelligence"
        )
        cursor.execute('''
            INSERT INTO users (name, email, password, interests)
            VALUES (?, ?, ?, ?)
        ''', demo_user)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print("Database initialized and migrated successfully at:", DB_PATH)
