// Settings page functionality
let currentUser = null;
let isAdmin = false;

// Load user profile and settings
async function loadProfile() {
    try {
        const response = await fetch(`${API_BASE}/auth/profile`, {
            credentials: 'include'
        });
        
        if (response.status === 401) {
            window.location.href = '/login.html';
            return;
        }
        
        currentUser = await response.json();
        isAdmin = currentUser.is_admin;
        
        // Update username display
        const usernameElement = document.getElementById('current-username');
        usernameElement.textContent = currentUser.username;
        
        // Update role badge
        const roleBadge = document.getElementById('user-role-badge');
        if (isAdmin) {
            roleBadge.textContent = 'ADMIN';
            roleBadge.style.background = 'var(--accent-color)';
            document.getElementById('user-management-section').style.display = 'flex';
            loadUsers();
        } else {
            roleBadge.textContent = 'USER';
            roleBadge.style.background = '#4a4a4a';
        }
        
        loadStoredFiles();
        
    } catch (error) {
        console.error('Error loading profile:', error);
        document.getElementById('current-username').textContent = 'Error loading user';
    }
}

// Theme toggle
function loadThemePreference() {
    const theme = localStorage.getItem('theme') || 'dark';
    const themeToggle = document.getElementById('theme-toggle');
    
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
        themeToggle.checked = true;
    } else {
        document.body.classList.add('light-theme');
        document.body.classList.remove('dark-theme');
        themeToggle.checked = false;
    }
}

// Setup theme toggle handler
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    
    // Load saved theme
    loadThemePreference();
    
    // Theme toggle change handler
    themeToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            // Switch to dark mode
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            // Switch to light mode
            document.body.classList.add('light-theme');
            document.body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Load profile
    loadProfile();
});

// Unified account form
document.getElementById('change-account-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const newUsername = document.getElementById('new-username').value.trim();
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    if (!currentPassword) {
        showAlert('Current password is required', 'error');
        return;
    }
    
    // Check if user wants to change password
    if (newPassword || confirmPassword) {
        if (newPassword !== confirmPassword) {
            showAlert('New passwords do not match', 'error');
            return;
        }
        if (newPassword.length < 8) {
            showAlert('New password must be at least 8 characters', 'error');
            return;
        }
    }
    
    let changesMade = false;
    
    // Change username if provided
    if (newUsername && newUsername.length >= 3) {
        try {
            const response = await fetch(`${API_BASE}/auth/change-username`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ 
                    new_username: newUsername,
                    password: currentPassword
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Username changed successfully!', 'success');
                document.getElementById('current-username').textContent = data.username;
                changesMade = true;
            } else {
                showAlert(data.error || 'Failed to change username', 'error');
                return;
            }
        } catch (error) {
            console.error('Change username error:', error);
            showAlert('Failed to change username', 'error');
            return;
        }
    }
    
    // Change password if provided
    if (newPassword) {
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
                showAlert('Password changed successfully!', 'success');
                changesMade = true;
            } else {
                showAlert(data.error || 'Failed to change password', 'error');
                return;
            }
        } catch (error) {
            console.error('Change password error:', error);
            showAlert('Failed to change password', 'error');
            return;
        }
    }
    
    if (!changesMade) {
        showAlert('No changes were made', 'error');
    } else {
        document.getElementById('change-account-form').reset();
    }
});

// Store M3U form
document.getElementById('store-m3u-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('m3u-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Please select a file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/playlists/store`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('M3U file stored successfully!', 'success');
            document.getElementById('store-m3u-form').reset();
            loadStoredFiles();
        } else {
            showAlert(data.error || 'Failed to store M3U file', 'error');
        }
    } catch (error) {
        console.error('Store M3U error:', error);
        showAlert('Failed to store M3U file', 'error');
    }
});

// Load stored M3U files
async function loadStoredFiles() {
    try {
        const response = await fetch(`${API_BASE}/playlists/stored`, {
            credentials: 'include'
        });
        
        const files = await response.json();
        const container = document.getElementById('stored-files-list');
        
        if (files.length === 0) {
            container.innerHTML = '<div class="empty-state">No stored files</div>';
            return;
        }
        
        container.innerHTML = files.map(file => `
            <div class="file-item">
                <div style="flex: 1; min-width: 0;">
                    <div class="file-item-name">${file.filename}</div>
                    <div class="file-item-details">${file.size_mb} MB • ${new Date(file.created).toLocaleDateString()}</div>
                </div>
                <div class="item-actions">
                    <a href="${API_BASE}/playlists/stored/${file.filename}/download" class="btn btn-primary btn-sm" download>⬇</a>
                    <button class="btn btn-secondary btn-sm" onclick="deleteStoredFile('${file.filename}')">🗑️</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading stored files:', error);
    }
}

// Delete stored M3U file
async function deleteStoredFile(filename) {
    if (!confirm(`Delete ${filename}?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/playlists/stored/${filename}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            showAlert('File deleted successfully', 'success');
            loadStoredFiles();
        } else {
            showAlert('Failed to delete file', 'error');
        }
    } catch (error) {
        console.error('Delete file error:', error);
        showAlert('Failed to delete file', 'error');
    }
}

// Load users (admin only)
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/auth/users`, {
            credentials: 'include'
        });
        
        if (!response.ok) return;
        
        const users = await response.json();
        const container = document.getElementById('user-list');
        
        if (users.length === 0) {
            container.innerHTML = '<div class="empty-state">No users</div>';
            return;
        }
        
        container.innerHTML = users.map(user => `
            <div class="user-item">
                <div style="flex: 1; min-width: 0;">
                    <div class="user-item-name">${user.username}</div>
                    <div class="user-item-role">${user.is_admin ? 'Admin' : 'User'}</div>
                </div>
                <div class="item-actions">
                    ${user.id !== currentUser.id ? `<button class="btn btn-secondary btn-sm" onclick="deleteUser(${user.id}, '${user.username}')">🗑️</button>` : '<span style="color: var(--text-secondary); font-size: 11px;">You</span>'}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Create user modal
document.getElementById('create-user-btn').addEventListener('click', () => {
    document.getElementById('create-user-modal').classList.remove('hidden');
});

document.getElementById('create-user-close').addEventListener('click', () => {
    document.getElementById('create-user-modal').classList.add('hidden');
});

// Create user form
document.getElementById('create-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        username: formData.get('username'),
        password: formData.get('password'),
        is_admin: formData.get('is_admin') === 'on'
    };
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('User created successfully!', 'success');
            document.getElementById('create-user-modal').classList.add('hidden');
            document.getElementById('create-user-form').reset();
            loadUsers();
        } else {
            showAlert(result.error || 'Failed to create user', 'error');
        }
    } catch (error) {
        console.error('Create user error:', error);
        showAlert('Failed to create user', 'error');
    }
});

// Delete user
async function deleteUser(userId, username) {
    if (!confirm(`Delete user "${username}"?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/auth/users/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            showAlert('User deleted successfully', 'success');
            loadUsers();
        } else {
            const data = await response.json();
            showAlert(data.error || 'Failed to delete user', 'error');
        }
    } catch (error) {
        console.error('Delete user error:', error);
        showAlert('Failed to delete user', 'error');
    }
}

function showAlert(message, type = 'error') {
    const container = document.getElementById('alert-container');
    container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    
    if (type === 'success') {
        setTimeout(() => {
            container.innerHTML = '';
        }, 5000);
    }
}

// Make functions global for onclick handlers
window.deleteStoredFile = deleteStoredFile;
window.deleteUser = deleteUser;
