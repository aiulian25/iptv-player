const API_BASE = '/api';

let currentUser = null;
let authCheckComplete = false;

// Check auth status on page load
async function checkAuth() {
    // Don't check on login/change-password pages
    const currentPage = window.location.pathname;
    if (currentPage === '/login.html' || currentPage === '/change-password.html' || currentPage === '/settings.html') {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/status`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        currentUser = data.authenticated ? data : null;
        authCheckComplete = true;
        
        // Update UI based on auth status
        updateUIBasedOnAuth(data.authenticated);
        
        console.log('Auth status:', data);
        
    } catch (error) {
        console.error('Auth check error:', error);
        currentUser = null;
        authCheckComplete = true;
        updateUIBasedOnAuth(false);
    }
}

function updateUIBasedOnAuth(isAuthenticated) {
    console.log('Updating UI, authenticated:', isAuthenticated);
    
    // Sidebar buttons
    const addPlaylistBtn = document.getElementById('add-playlist-btn');
    const loginLinkBtn = document.getElementById('login-link-btn');
    
    // Header buttons
    const loginBtn = document.getElementById('login-btn');
    const settingsBtn = document.getElementById('settings-btn');
    const recordBtn = document.getElementById('record-btn');
    const recordingsBtn = document.getElementById('recordings-btn');
    const logoutBtn = document.getElementById('logout-btn');
    
    if (isAuthenticated) {
        // Hide login buttons, show management buttons
        if (addPlaylistBtn) addPlaylistBtn.classList.remove('hidden');
        if (loginLinkBtn) loginLinkBtn.classList.add('hidden');
        if (loginBtn) loginBtn.classList.add('hidden');
        if (settingsBtn) settingsBtn.classList.remove('hidden');
        if (recordBtn) recordBtn.classList.remove('hidden');
        if (recordingsBtn) recordingsBtn.classList.remove('hidden');
        if (logoutBtn) logoutBtn.classList.remove('hidden');
    } else {
        // Show login buttons, hide management buttons
        if (addPlaylistBtn) addPlaylistBtn.classList.add('hidden');
        if (loginLinkBtn) loginLinkBtn.classList.remove('hidden');
        if (loginBtn) loginBtn.classList.remove('hidden');
        if (settingsBtn) settingsBtn.classList.add('hidden');
        if (recordBtn) recordBtn.classList.add('hidden');
        if (recordingsBtn) recordingsBtn.classList.add('hidden');
        if (logoutBtn) logoutBtn.classList.add('hidden');
    }
}

function requireAuth() {
    if (!authCheckComplete) {
        alert('Checking authentication...');
        return false;
    }
    
    if (!currentUser) {
        if (confirm('Please login to access this feature. Go to login page?')) {
            window.location.href = '/login.html';
        }
        return false;
    }
    
    if (currentUser.must_change_password) {
        alert('Please change your password first');
        window.location.href = '/change-password.html';
        return false;
    }
    
    return true;
}

// Login form handler
if (document.getElementById('login-form')) {
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                if (data.user.must_change_password) {
                    window.location.href = '/change-password.html';
                } else {
                    window.location.href = '/';
                }
            } else {
                showAlert(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            showAlert('Login failed. Please try again.', 'error');
        }
    });
}

// Change password form handler
if (document.getElementById('change-password-form') && !document.getElementById('new-username')) {
    document.getElementById('change-password-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        if (newPassword !== confirmPassword) {
            showAlert('New passwords do not match', 'error');
            return;
        }
        
        if (newPassword.length < 8) {
            showAlert('Password must be at least 8 characters', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/auth/change-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ 
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Password changed successfully! You can now use all features.');
                window.location.href = '/';
            } else {
                showAlert(data.error || 'Password change failed', 'error');
            }
        } catch (error) {
            console.error('Password change error:', error);
            showAlert('Password change failed. Please try again.', 'error');
        }
    });
}

function showAlert(message, type = 'error') {
    const container = document.getElementById('alert-container');
    if (container) {
        container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    }
}

// Initialize auth check when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, checking auth...');
        checkAuth();
    });
} else {
    console.log('DOM already loaded, checking auth...');
    checkAuth();
}

// Export for global access
window.requireAuth = requireAuth;
window.currentUser = currentUser;
