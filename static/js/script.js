/**
 * The E-Library - Client Side JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // 2. Confirmation dialogs for dangerous actions (delete book)
    const deleteButtons = document.querySelectorAll('.btn-confirm-delete');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const itemName = this.getAttribute('data-item-name') || 'this book';
            if (!confirm(`Are you sure you want to permanently delete "${itemName}" from the catalog?`)) {
                e.preventDefault();
            }
        });
    });

    // 3. Return book confirmation
    const returnButtons = document.querySelectorAll('.btn-confirm-return');
    returnButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const bookTitle = this.getAttribute('data-book-title') || 'this book';
            if (!confirm(`Confirm returning "${bookTitle}" to the library?`)) {
                e.preventDefault();
            }
        });
    });

    // 4. Client validation for interest chips during registration
    const registerForm = document.querySelector('#registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function (e) {
            const checkedInterests = registerForm.querySelectorAll('input[name="interests"]:checked');
            if (checkedInterests.length === 0) {
                e.preventDefault();
                alert('Please select at least one area of interest so our AI can recommend relevant books to you!');
            }
        });
    }

    // 5. Quick admin demo credentials autofill helper if on login page
    const fillAdminBtn = document.getElementById('fillAdminCredentials');
    if (fillAdminBtn) {
        fillAdminBtn.addEventListener('click', function () {
            const emailField = document.getElementById('adminEmail');
            const passField = document.getElementById('adminPassword');
            if (emailField && passField) {
                emailField.value = 'admin@elibrary.com';
                passField.value = 'admin123';
            }
        });
    }

    // 6. Quick student demo credentials autofill helper
    const fillStudentBtn = document.getElementById('fillStudentCredentials');
    if (fillStudentBtn) {
        fillStudentBtn.addEventListener('click', function () {
            const emailField = document.getElementById('studentEmail');
            const passField = document.getElementById('studentPassword');
            if (emailField && passField) {
                emailField.value = 'student@elibrary.com';
                passField.value = 'student123';
            }
        });
    }
});
