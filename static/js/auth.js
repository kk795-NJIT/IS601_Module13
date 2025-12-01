document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    const loginForm = document.getElementById('loginForm');
    const messageDiv = document.getElementById('message');

    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(registerForm);
            const data = Object.fromEntries(formData.entries());

            if (data.password !== data.confirmPassword) {
                showMessage("Passwords do not match", "error");
                return;
            }

            // Remove confirmPassword before sending
            delete data.confirmPassword;

            try {
                const response = await fetch('/users/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    showMessage("Registration successful! Redirecting to login...", "success");
                    setTimeout(() => {
                        window.location.href = '/static/login.html';
                    }, 2000);
                } else {
                    const errorData = await response.json();
                    showMessage(errorData.detail || "Registration failed", "error");
                }
            } catch (error) {
                showMessage("An error occurred. Please try again.", "error");
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch('/users/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    const result = await response.json();
                    localStorage.setItem('token', result.access_token);
                    showMessage("Login successful!", "success");
                    // Redirect or update UI
                } else {
                    const errorData = await response.json();
                    showMessage(errorData.detail || "Login failed", "error");
                }
            } catch (error) {
                showMessage("An error occurred. Please try again.", "error");
            }
        });
    }
});