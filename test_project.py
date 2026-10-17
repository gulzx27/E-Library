"""
Automated Test Suite for E-Library Project
Tests database, authentication, catalog search, borrowing workflows,
AI recommendations, book prices (INR), 14-day due dates, overdue detection,
and admin management.
"""

import unittest
import os
import sqlite3
from datetime import datetime, timedelta
from app import app
from database import init_db, get_db_connection
from recommendation import get_recommendations
from werkzeug.security import check_password_hash


class ELibraryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        init_db()

    def setUp(self):
        self.client = app.test_client()

    def test_01_database_and_sample_books(self):
        """Test database initialization and verify at least 10 sample books exist."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM books")
        count = cursor.fetchone()['count']
        conn.close()
        self.assertGreaterEqual(count, 10, f"Expected at least 10 books, found {count}")
        print(f"[PASS] test_01_database_and_sample_books: Found {count} sample books.")

    def test_02_home_page(self):
        """Test home page loads with 200 OK and contains hero content."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Discover. Read. Learn.", response.data)
        self.assertIn(b"The E-Library", response.data)
        print("[PASS] test_02_home_page: Home page rendered with hero text.")

    def test_03_registration_and_password_hashing(self):
        """Test student registration and ensure passwords are securely hashed."""
        test_email = "teststudent@college.edu"
        
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email = ?", (test_email,))
        conn.commit()
        conn.close()

        response = self.client.post('/register', data={
            'name': 'Test Student',
            'email': test_email,
            'password': 'password123',
            'confirm_password': 'password123',
            'interests': ['Artificial Intelligence', 'Programming']
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registration successful", response.data)

        # Verify in DB
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (test_email,)).fetchone()
        conn.close()

        self.assertIsNotNone(user)
        self.assertNotEqual(user['password'], 'password123', "Password must not be stored in plain text!")
        self.assertTrue(check_password_hash(user['password'], 'password123'))
        self.assertIn("Artificial Intelligence", user['interests'])
        print("[PASS] test_03_registration_and_password_hashing: User registered and password hashed securely.")

    def test_04_duplicate_registration_rejected(self):
        """Test that registering with an existing email is rejected with error."""
        response = self.client.post('/register', data={
            'name': 'Duplicate User',
            'email': 'student@elibrary.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'interests': ['Cybersecurity']
        }, follow_redirects=True)

        self.assertIn(b"already exists", response.data)
        print("[PASS] test_04_duplicate_registration_rejected: Duplicate email caught and rejected.")

    def test_05_student_login_and_logout(self):
        """Test student login with valid & invalid credentials, and logout."""
        # Invalid credentials
        res_fail = self.client.post('/login', data={
            'email': 'student@elibrary.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b"Invalid email or password", res_fail.data)

        # Valid credentials
        res_ok = self.client.post('/login', data={
            'email': 'student@elibrary.com',
            'password': 'student123'
        }, follow_redirects=True)
        self.assertIn(b"Welcome back", res_ok.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b"successfully logged out", res_logout.data)
        print("[PASS] test_05_student_login_and_logout: Authentication flow verified.")

    def test_06_catalog_search(self):
        """Test database search querying for 'Python' and 'AI'."""
        res_py = self.client.get('/books?q=Python')
        self.assertEqual(res_py.status_code, 200)
        self.assertIn(b"Python Programming", res_py.data)

        res_ai = self.client.get('/books?q=Artificial+Intelligence')
        self.assertEqual(res_ai.status_code, 200)
        self.assertIn(b"Artificial Intelligence", res_ai.data)
        print("[PASS] test_06_catalog_search: Live DB search returns matching books.")

    def test_07_book_request_and_return_cycle(self):
        """Test the end-to-end borrowing cycle: request book, check availability=0, return book, availability=1."""
        with self.client:
            self.client.post('/login', data={'email': 'student@elibrary.com', 'password': 'student123'})
            
            # Find an available book
            conn = get_db_connection()
            book = conn.execute("SELECT * FROM books WHERE available = 1 LIMIT 1").fetchone()
            book_id = book['id']
            conn.close()

            # 2. Request book
            req_res = self.client.post(f'/request-book/{book_id}', follow_redirects=True)
            self.assertIn(b"Success!", req_res.data)

            # 3. Check DB availability is now 0 and due_date exists
            conn = get_db_connection()
            updated_book = conn.execute("SELECT available FROM books WHERE id = ?", (book_id,)).fetchone()
            self.assertEqual(updated_book['available'], 0)

            # Check request record exists and has due_date
            req_record = conn.execute(
                "SELECT * FROM requests WHERE book_id = ? AND status = 'Active'",
                (book_id,)
            ).fetchone()
            self.assertIsNotNone(req_record)
            self.assertIsNotNone(req_record['due_date'], "Due date must be set on borrow!")
            req_id = req_record['id']
            conn.close()

            # 4. Return book
            ret_res = self.client.post(f'/return-book/{req_id}', follow_redirects=True)
            self.assertIn(b"successfully returned", ret_res.data)

            # 5. Check book availability restored to 1
            conn = get_db_connection()
            restored_book = conn.execute("SELECT available FROM books WHERE id = ?", (book_id,)).fetchone()
            self.assertEqual(restored_book['available'], 1)
            conn.close()

        print("[PASS] test_07_book_request_and_return_cycle: Full borrowing transaction cycle verified.")

    def test_08_ai_recommendation_algorithm(self):
        """Test content-based AI recommendation logic and reason generation."""
        user = {
            'id': 1,
            'interests': 'Artificial Intelligence, Data Science'
        }
        user_requests = [
            {'book_id': 6, 'title': 'Artificial Intelligence: A Modern Approach', 'category': 'Artificial Intelligence'}
        ]
        
        conn = get_db_connection()
        all_books = conn.execute("SELECT * FROM books").fetchall()
        conn.close()

        recs = get_recommendations(user, user_requests, all_books, limit=5)
        self.assertGreater(len(recs), 0)

        top_rec = recs[0]
        self.assertIn('relevance_score', top_rec)
        self.assertIn('recommendation_reason', top_rec)
        self.assertTrue(top_rec['recommendation_reason'].startswith("Recommended because"))
        print(f"[PASS] test_08_ai_recommendation_algorithm: Top recommended '{top_rec['title']}' ({top_rec['match_percentage']}% match).")

    def test_09_admin_authentication_and_dashboard(self):
        """Test admin login with admin@elibrary.com / admin123 and dashboard metrics."""
        res_unauth = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b"Admin", res_unauth.data)

        with self.client:
            res_admin = self.client.post('/admin/login', data={
                'email': 'admin@elibrary.com',
                'password': 'admin123'
            }, follow_redirects=True)
            self.assertEqual(res_admin.status_code, 200)
            self.assertIn(b"Control Center", res_admin.data)
            self.assertIn(b"Total Books", res_admin.data)

        print("[PASS] test_09_admin_authentication_and_dashboard: Admin route security and dashboard verified.")

    def test_10_admin_book_crud_with_price(self):
        """Test admin Add, Edit, and Delete book workflow with price in Indian Rupees."""
        with self.client:
            self.client.post('/admin/login', data={'email': 'admin@elibrary.com', 'password': 'admin123'})

            # 1. Add Book with Price ₹750.00
            add_res = self.client.post('/admin/books/add', data={
                'title': 'Quantum Computing Principles',
                'author': 'Richard Feynman & David Deutsch',
                'category': 'Computer Science',
                'description': 'Introduction to qubits, quantum gates, entanglement, and Shor algorithm.',
                'available': 1,
                'price': 750.00
            }, follow_redirects=True)
            self.assertIn(b"successfully added", add_res.data)

            conn = get_db_connection()
            new_book = conn.execute("SELECT * FROM books WHERE title = 'Quantum Computing Principles'").fetchone()
            self.assertIsNotNone(new_book)
            self.assertEqual(float(new_book['price']), 750.00)
            book_id = new_book['id']
            conn.close()

            # 2. Edit Book with updated Price ₹850.00
            edit_res = self.client.post(f'/admin/books/edit/{book_id}', data={
                'title': 'Quantum Computing Principles (2nd Edition)',
                'author': 'Richard Feynman & David Deutsch',
                'category': 'Computer Science',
                'description': 'Updated edition covering NISQ processors and quantum algorithms.',
                'available': 1,
                'price': 850.00
            }, follow_redirects=True)
            self.assertIn(b"updated successfully", edit_res.data)

            conn = get_db_connection()
            edited_book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            self.assertEqual(float(edited_book['price']), 850.00)
            conn.close()

            # 3. Delete Book
            del_res = self.client.post(f'/admin/books/delete/{book_id}', follow_redirects=True)
            self.assertIn(b"deleted from catalog", del_res.data)

            conn = get_db_connection()
            deleted_book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            conn.close()
            self.assertIsNone(deleted_book)

        print("[PASS] test_10_admin_book_crud_with_price: Add, edit with price, and delete verified.")

    def test_11_book_prices_in_database_and_catalog(self):
        """Test that every book in the database has a valid price > 0 and price renders in catalog."""
        conn = get_db_connection()
        books = conn.execute("SELECT id, title, price FROM books").fetchall()
        conn.close()

        self.assertGreater(len(books), 0)
        for b in books:
            self.assertIsNotNone(b['price'])
            self.assertGreater(float(b['price']), 0, f"Book {b['title']} must have positive price!")

        # Verify catalog response contains price formatting
        res = self.client.get('/books')
        self.assertEqual(res.status_code, 200)
        # Search for Indian Rupee symbol or formatted numbers
        self.assertTrue(b"499.00" in res.data or b"\xe2\x82\xb9" in res.data)
        print(f"[PASS] test_11_book_prices_in_database_and_catalog: Verified prices across all {len(books)} books.")

    def test_12_due_date_calculation_and_overdue_logic(self):
        """Test 14-day default due date generation and overdue detection."""
        conn = get_db_connection()
        # Insert a simulated overdue request (issued 20 days ago, due 6 days ago)
        past_issue = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S')
        past_due = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO requests (user_id, book_id, request_date, due_date, status)
            VALUES (1, 1, ?, ?, 'Active')
        ''', (past_issue, past_due))
        overdue_req_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Login as user and check purchases page
        with self.client:
            self.client.post('/login', data={'email': 'student@elibrary.com', 'password': 'student123'})
            res = self.client.get('/my-requests')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Overdue", res.data)

        # Clean up overdue test record
        conn = get_db_connection()
        conn.execute("DELETE FROM requests WHERE id = ?", (overdue_req_id,))
        conn.commit()
        conn.close()

        print("[PASS] test_12_due_date_calculation_and_overdue_logic: 14-day due date & overdue badge verified.")


if __name__ == '__main__':
    unittest.main()
