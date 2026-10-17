"""
The E-Library - Online Library Management System with AI-Based Book Recommendation
Flask Application Backend
"""

import os
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db
from recommendation import get_recommendations

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.secret_key = os.environ.get('SECRET_KEY', 'elibrary_cse_capstone_secure_token_987654')

# Expose WSGI application object for PythonAnywhere and production WSGI servers
application = app

# Ensure database tables and migrations are initialized upon WSGI startup without resetting data
with app.app_context():
    init_db()

# Predefined Admin Credentials for local college project prototype
ADMIN_EMAIL = "admin@elibrary.com"
ADMIN_PASSWORD = "admin123"

# Available interest areas for registration & filtering
INTEREST_OPTIONS = [
    "Programming",
    "Artificial Intelligence",
    "Data Science",
    "Cybersecurity",
    "Networking",
    "Web Development",
    "Database",
    "Cloud Computing",
    "Computer Science"
]


# ---------------------------------------------------------
# Custom Decorators for Access Control
# ---------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Unauthorized access! Library Admin privileges required.", "danger")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------
# Custom Template Filters & Helpers
# ---------------------------------------------------------

@app.template_filter('format_date')
def format_date_filter(value):
    """Format timestamps or date strings into readable '31 Oct 2026' format."""
    if not value:
        return '-'
    if isinstance(value, str):
        try:
            clean_val = value.split('.')[0]
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(clean_val, fmt)
                    return dt.strftime('%d %b %Y')
                except ValueError:
                    continue
        except Exception:
            pass
        return value[:10]
    elif hasattr(value, 'strftime'):
        return value.strftime('%d %b %Y')
    return str(value)


@app.template_filter('format_price')
def format_price_filter(value):
    """Format numeric values as Indian Rupee currency (e.g. ₹499.00)."""
    try:
        val_float = float(value)
        return f"₹{val_float:,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"


def enrich_request(req):
    """
    Enrich raw request row/dict with overdue calculation and date formatting helpers.
    Sets is_overdue=True if active and current time has passed due_date.
    """
    if req is None:
        return {}
    d = dict(req)
    now = datetime.now()
    due_date_str = d.get('due_date')
    is_overdue = False

    if d.get('status') == 'Active' and due_date_str:
        try:
            clean_val = str(due_date_str).split('.')[0]
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(clean_val, fmt)
                    if now > dt:
                        is_overdue = True
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    d['is_overdue'] = is_overdue
    return d


# ---------------------------------------------------------
# Context Processor for Global Template Variables
# ---------------------------------------------------------

@app.context_processor
def inject_global_data():
    return {
        'is_logged_in': 'user_id' in session,
        'user_name': session.get('user_name', ''),
        'user_email': session.get('user_email', ''),
        'is_admin': session.get('is_admin', False),
        'interest_options': INTEREST_OPTIONS
    }


# ---------------------------------------------------------
# Public Routes
# ---------------------------------------------------------

@app.route('/')
def index():
    """Home Page with hero section, statistics, and featured books."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Statistics for dashboard display
    cursor.execute("SELECT COUNT(*) AS total_books FROM books")
    total_books = cursor.fetchone()['total_books']

    cursor.execute("SELECT COUNT(*) AS available_books FROM books WHERE available = 1")
    available_books = cursor.fetchone()['available_books']

    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    # Fetch 6 featured books for the home showcase
    cursor.execute("SELECT * FROM books ORDER BY id DESC LIMIT 6")
    featured_books = cursor.fetchall()
    conn.close()

    return render_template(
        'index.html',
        total_books=total_books,
        available_books=available_books,
        total_users=total_users,
        featured_books=featured_books
    )


# ---------------------------------------------------------
# Authentication Routes (Normal Student / User)
# ---------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student Registration with Interests selection and secure password hashing."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        interests_list = request.form.getlist('interests')

        # Form validation
        if not name or not email or not password or not confirm_password:
            flash("Please fill in all required fields.", "danger")
            return render_template('register.html', name=name, email=email, selected_interests=interests_list)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html', name=name, email=email, selected_interests=interests_list)

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter.", "danger")
            return render_template('register.html', name=name, email=email, selected_interests=interests_list)

        if not interests_list:
            flash("Please select at least one area of interest for personalized recommendations.", "warning")
            return render_template('register.html', name=name, email=email, selected_interests=[])

        interests_str = ", ".join(interests_list)
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for duplicate email
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash("An account with this email address already exists. Please log in.", "warning")
            return render_template('register.html', name=name, email=email, selected_interests=interests_list)

        try:
            cursor.execute('''
                INSERT INTO users (name, email, password, interests)
                VALUES (?, ?, ?, ?)
            ''', (name, email, hashed_password, interests_str))
            conn.commit()
            conn.close()

            flash("Registration successful! You can now log in with your credentials.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            conn.close()
            flash(f"Error registering user: {str(e)}", "danger")
            return render_template('register.html', name=name, email=email, selected_interests=interests_list)

    return render_template('register.html', selected_interests=[])


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Student Login with password verification and session initialization."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('login.html', email=email)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['interests'] = user['interests']
            session['is_admin'] = False

            flash(f"Welcome back, {user['name']}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash("Invalid email or password. Please check your credentials.", "danger")
            return render_template('login.html', email=email)

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout current user or admin and clear session."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('index'))


# ---------------------------------------------------------
# User Dashboard & Profile
# ---------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    """User Dashboard showing quick statistics, recommendations preview, and recent requests."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # User details
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()

    # User's requests with price and due_date
    cursor.execute('''
        SELECT r.id, r.request_date, r.due_date, r.return_date, r.status,
               b.id AS book_id, b.title, b.author, b.category, b.price
        FROM requests r
        JOIN books b ON r.book_id = b.id
        WHERE r.user_id = ?
        ORDER BY r.request_date DESC
    ''', (session['user_id'],))
    raw_user_requests = cursor.fetchall()
    user_requests = [enrich_request(r) for r in raw_user_requests]

    # Count statistics
    active_requests_count = sum(1 for r in user_requests if r['status'] == 'Active')
    overdue_count = sum(1 for r in user_requests if r['is_overdue'])
    total_requested_count = len(user_requests)

    # All books in library
    cursor.execute("SELECT * FROM books")
    all_books = cursor.fetchall()
    total_available_books = sum(1 for b in all_books if b['available'] == 1)

    # Generate Top 4 AI Recommendations for Dashboard widget
    recommendations = get_recommendations(user, user_requests, all_books, limit=4, exclude_requested=True)

    conn.close()

    return render_template(
        'dashboard.html',
        user=user,
        active_requests_count=active_requests_count,
        overdue_count=overdue_count,
        total_requested_count=total_requested_count,
        total_available_books=total_available_books,
        recent_requests=user_requests[:4],
        recommendations=recommendations
    )


# ---------------------------------------------------------
# Book Catalog & Search Functionality
# ---------------------------------------------------------

@app.route('/books')
def books():
    """Catalog of all books with live database search, prices, and category filters."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM books WHERE 1=1"
    params = []

    if query:
        search_pattern = f"%{query}%"
        sql += " AND (title LIKE ? OR author LIKE ? OR category LIKE ? OR description LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY title ASC"

    cursor.execute(sql, params)
    book_list = cursor.fetchall()

    # Get distinct categories for filter buttons
    cursor.execute("SELECT DISTINCT category FROM books ORDER BY category ASC")
    categories = [row['category'] for row in cursor.fetchall()]

    # If user is logged in, find what books they have already requested
    user_requested_book_ids = set()
    if 'user_id' in session:
        cursor.execute("SELECT book_id FROM requests WHERE user_id = ? AND status = 'Active'", (session['user_id'],))
        user_requested_book_ids = {row['book_id'] for row in cursor.fetchall()}

    conn.close()

    return render_template(
        'books.html',
        books=book_list,
        search_query=query,
        selected_category=category,
        categories=categories,
        user_requested_book_ids=user_requested_book_ids
    )


# ---------------------------------------------------------
# Book Request & Borrowing Workflow (Issue & Due Date)
# ---------------------------------------------------------

@app.route('/request-book/<int:book_id>', methods=['POST', 'GET'])
@login_required
def request_book(book_id):
    """
    Handle book request/issue transaction:
    Verifies availability, records issue_date and calculates default due_date (14 days).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if book exists
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()

    if not book:
        conn.close()
        flash("The requested book was not found in the library catalog.", "danger")
        return redirect(url_for('books'))

    # Check availability
    if book['available'] != 1:
        conn.close()
        flash(f"Sorry, '{book['title']}' is currently not available or already issued.", "warning")
        return redirect(url_for('books'))

    # Check if user already has an active request for this book
    cursor.execute('''
        SELECT id FROM requests
        WHERE user_id = ? AND book_id = ? AND status = 'Active'
    ''', (session['user_id'], book_id))
    existing_request = cursor.fetchone()

    if existing_request:
        conn.close()
        flash(f"You already have an active loan for '{book['title']}'. Check 'My Requests'.", "info")
        return redirect(url_for('my_requests'))

    try:
        now = datetime.now()
        due_date = now + timedelta(days=14)
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        due_str = due_date.strftime('%Y-%m-%d %H:%M:%S')

        # 1. Create request record with 14-day default due date
        cursor.execute('''
            INSERT INTO requests (user_id, book_id, request_date, due_date, status)
            VALUES (?, ?, ?, ?, 'Active')
        ''', (session['user_id'], book_id, now_str, due_str))

        # 2. Update book availability to 0 (Not Available)
        cursor.execute("UPDATE books SET available = 0 WHERE id = ?", (book_id,))

        conn.commit()
        conn.close()

        formatted_due = due_date.strftime('%d %b %Y')
        flash(f"Success! You have requested '{book['title']}'. Issued today; Due Date is {formatted_due} (14 days loan period).", "success")
        return redirect(url_for('my_requests'))
    except Exception as e:
        conn.close()
        flash(f"An error occurred while processing your request: {str(e)}", "danger")
        return redirect(url_for('books'))


@app.route('/return-book/<int:request_id>', methods=['POST', 'GET'])
@login_required
def return_book(request_id):
    """Return an issued book, recording return_date and restoring its catalog availability."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.*, b.title, b.id AS book_id
        FROM requests r
        JOIN books b ON r.book_id = b.id
        WHERE r.id = ? AND r.user_id = ?
    ''', (request_id, session['user_id']))
    req = cursor.fetchone()

    if not req:
        conn.close()
        flash("Transaction record not found or access denied.", "danger")
        return redirect(url_for('my_requests'))

    if req['status'] == 'Returned':
        conn.close()
        flash("This book has already been marked as returned.", "info")
        return redirect(url_for('my_requests'))

    try:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Mark request as Returned with return timestamp
        cursor.execute("UPDATE requests SET status = 'Returned', return_date = ? WHERE id = ?", (now_str, request_id))
        # Restore book availability
        cursor.execute("UPDATE books SET available = 1 WHERE id = ?", (req['book_id'],))
        conn.commit()
        conn.close()

        flash(f"'{req['title']}' has been successfully returned! Availability has been restored in the catalog.", "success")
        return redirect(url_for('my_requests'))
    except Exception as e:
        conn.close()
        flash(f"Error returning book: {str(e)}", "danger")
        return redirect(url_for('my_requests'))


@app.route('/my-requests')
@login_required
def my_requests():
    """Display student's borrowed books with issue date, due date, price, and overdue status."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.id AS request_id, r.request_date, r.due_date, r.return_date, r.status,
               b.id AS book_id, b.title, b.author, b.category, b.price, b.available
        FROM requests r
        JOIN books b ON r.book_id = b.id
        WHERE r.user_id = ?
        ORDER BY r.request_date DESC
    ''', (session['user_id'],))
    raw_requests = cursor.fetchall()
    requests_list = [enrich_request(r) for r in raw_requests]
    conn.close()

    return render_template('purchases.html', requests=requests_list)


# ---------------------------------------------------------
# AI-Based Book Recommendations Page
# ---------------------------------------------------------

@app.route('/recommendations')
@login_required
def recommendations():
    """Dedicated AI-Based Book Recommendations page explaining relevance score, price, and matching rationale."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # User details
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()

    # User's request history
    cursor.execute('''
        SELECT r.book_id, r.status, b.title, b.category, b.description
        FROM requests r
        JOIN books b ON r.book_id = b.id
        WHERE r.user_id = ?
    ''', (session['user_id'],))
    user_requests = cursor.fetchall()

    # All library books (including prices)
    cursor.execute("SELECT * FROM books")
    all_books = cursor.fetchall()
    conn.close()

    # Run AI content-based recommendation system
    recommended_books = get_recommendations(user, user_requests, all_books, limit=12, exclude_requested=True)

    # Parse user interests for badge display
    interests_display = [i.strip() for i in user['interests'].split(',') if i.strip()] if user['interests'] else []

    return render_template(
        'recommendations.html',
        recommendations=recommended_books,
        user=user,
        interests=interests_display
    )


# ---------------------------------------------------------
# Admin Portal & Management
# ---------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin Login authentication."""
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session.clear()
            session['is_admin'] = True
            session['user_name'] = "Library Administrator"
            session['user_email'] = ADMIN_EMAIL
            flash("Logged in successfully as Administrator.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid administrator credentials. Access restricted.", "danger")
            return render_template('admin_login.html', email=email)

    return render_template('admin_login.html')


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Administrator Dashboard with metrics, book prices, due dates, user directory, and return tracking."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Metric Counts
    cursor.execute("SELECT COUNT(*) AS count FROM books")
    total_books = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM books WHERE available = 1")
    available_books = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM users")
    total_users = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM requests")
    total_requests = cursor.fetchone()['count']

    # 2. All Books (including price)
    cursor.execute("SELECT * FROM books ORDER BY id DESC")
    books_list = cursor.fetchall()

    # 3. All Users
    cursor.execute("SELECT id, name, email, interests, created_at FROM users ORDER BY id DESC")
    users_list = cursor.fetchall()

    # 4. All Requests with User, Book, Price, Issue Date, Due Date, and Return Date
    cursor.execute('''
        SELECT r.id AS request_id, r.request_date, r.due_date, r.return_date, r.status,
               u.name AS user_name, u.email AS user_email,
               b.id AS book_id, b.title AS book_title, b.category AS book_category, b.price AS book_price, b.available
        FROM requests r
        JOIN users u ON r.user_id = u.id
        JOIN books b ON r.book_id = b.id
        ORDER BY r.request_date DESC
    ''')
    raw_requests = cursor.fetchall()
    requests_list = [enrich_request(r) for r in raw_requests]

    conn.close()

    return render_template(
        'admin_dashboard.html',
        total_books=total_books,
        available_books=available_books,
        total_users=total_users,
        total_requests=total_requests,
        books=books_list,
        users=users_list,
        requests=requests_list,
        interest_options=INTEREST_OPTIONS
    )


@app.route('/admin/books/add', methods=['POST'])
@admin_required
def admin_add_book():
    """Add a new book to the library catalog with price in Indian Rupees (₹)."""
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    category = request.form.get('category', '').strip()
    description = request.form.get('description', '').strip()
    available = int(request.form.get('available', 1))

    try:
        price = float(request.form.get('price', 450.0))
        if price < 0:
            price = 450.0
    except (ValueError, TypeError):
        price = 450.0

    if not title or not author or not category or not description:
        flash("All fields are required to add a book.", "danger")
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO books (title, author, category, description, available, price)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, author, category, description, available, price))
    conn.commit()
    conn.close()

    flash(f"Book '{title}' successfully added with price ₹{price:,.2f}!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/books/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_book(book_id):
    """Edit existing book details in catalog, including Indian Rupee price."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()

    if not book:
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        available = int(request.form.get('available', 1))

        try:
            price = float(request.form.get('price', book['price'] if 'price' in book.keys() else 450.0))
            if price < 0:
                price = 450.0
        except (ValueError, TypeError):
            price = 450.0

        if not title or not author or not category or not description:
            conn.close()
            flash("All fields are required.", "danger")
            return render_template('admin_edit_book.html', book=book)

        cursor.execute('''
            UPDATE books
            SET title = ?, author = ?, category = ?, description = ?, available = ?, price = ?
            WHERE id = ?
        ''', (title, author, category, description, available, price, book_id))
        conn.commit()
        conn.close()

        flash(f"Book '{title}' details updated successfully (Price: ₹{price:,.2f})!", "success")
        return redirect(url_for('admin_dashboard'))

    conn.close()
    return render_template('admin_edit_book.html', book=book)


@app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
@admin_required
def admin_delete_book(book_id):
    """Delete a book from library catalog."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT title FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()

    if not book:
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    cursor.execute("DELETE FROM requests WHERE book_id = ?", (book_id,))
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    flash(f"Book '{book['title']}' deleted from catalog.", "info")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/requests/update-status/<int:request_id>', methods=['POST'])
@admin_required
def admin_update_request_status(request_id):
    """
    Admin endpoint to update request status.
    When marked 'Returned', records return_date and restores book availability to 1.
    """
    new_status = request.form.get('status', 'Active')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
    req = cursor.fetchone()

    if req:
        if new_status == 'Returned':
            cursor.execute("UPDATE requests SET status = 'Returned', return_date = ? WHERE id = ?", (now_str, request_id))
            cursor.execute("UPDATE books SET available = 1 WHERE id = ?", (req['book_id'],))
        elif new_status == 'Cancelled':
            cursor.execute("UPDATE requests SET status = 'Cancelled' WHERE id = ?", (request_id,))
            cursor.execute("UPDATE books SET available = 1 WHERE id = ?", (req['book_id'],))
        elif new_status in ['Active', 'Approved']:
            cursor.execute("UPDATE requests SET status = 'Active', return_date = NULL WHERE id = ?", (request_id,))
            cursor.execute("UPDATE books SET available = 0 WHERE id = ?", (req['book_id'],))

        conn.commit()
        flash(f"Request #{request_id} updated to status '{new_status}'.", "success")
    else:
        flash("Request record not found.", "danger")

    conn.close()
    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# ---------------------------------------------------------
# Application Entry Point (Local Development)
# ---------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
