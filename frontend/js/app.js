// Use API_BASE from auth.js

class IPTVApp {
    constructor() {
        this.currentPlaylist = null;
        this.currentChannel = null;
        this.channels = [];
        this.playlists = [];
        this.selectedChannels = new Set();
        this.activeRecordingId = null;
        this.contextMenuChannel = null;
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    async init() {
        console.log('Initializing IPTV App...');
        
        // Check authentication first
        await this.checkAuthBeforeInit();
        
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.setupContextMenu();
        await this.loadPlaylists();
        this.setupTheme();
    }
    
    async checkAuthBeforeInit() {
        try {
            const response = await fetch(`${API_BASE}/auth/status`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (!data.authenticated) {
                console.log('User not authenticated, redirecting to login...');
                window.location.href = '/login.html';
                return;
            }
            
            if (data.must_change_password) {
                console.log('User must change password, redirecting...');
                window.location.href = '/change-password.html';
                return;
            }
            
            console.log('User authenticated:', data.username);
            
        } catch (error) {
            console.error('Auth check error:', error);
            window.location.href = '/login.html';
        }
    }
    
    setupTheme() {
        const theme = localStorage.getItem('theme') || 'dark';
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
        } else {
            document.body.classList.add('light-theme');
            document.body.classList.remove('dark-theme');
        }
    }
    
    setupContextMenu() {
        const contextMenu = document.getElementById('context-menu');
        const contextFavorite = document.getElementById('context-favorite');
        const contextRemoveFavorite = document.getElementById('context-remove-favorite');
        
        // Hide context menu when clicking elsewhere
        document.addEventListener('click', () => {
            contextMenu.classList.add('hidden');
        });
        
        // Context menu actions
        contextFavorite.addEventListener('click', async () => {
            if (this.contextMenuChannel) {
                await this.toggleFavorite(this.contextMenuChannel.id);
            }
            contextMenu.classList.add('hidden');
        });
        
        contextRemoveFavorite.addEventListener('click', async () => {
            if (this.contextMenuChannel) {
                await this.toggleFavorite(this.contextMenuChannel.id);
            }
            contextMenu.classList.add('hidden');
        });
    }
    
    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
                document.getElementById(`${tabName}-tab`).classList.add('active');
                
                if (tabName === 'favorites') {
                    this.loadFavorites();
                } else if (tabName === 'channels' && this.currentPlaylist) {
                    this.loadChannels(this.currentPlaylist);
                }
            });
        });
        
        // Login buttons
        const loginBtn = document.getElementById('login-btn');
        if (loginBtn) {
            loginBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = '/login.html';
            });
        }
        
        const loginLinkBtn = document.getElementById('login-link-btn');
        if (loginLinkBtn) {
            loginLinkBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = '/login.html';
            });
        }
        
        // Settings button
        const settingsBtn = document.getElementById('settings-btn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = '/settings.html';
            });
        }
        
        // Favorite star button
        const favoriteStar = document.getElementById('favorite-star');
        if (favoriteStar) {
            favoriteStar.addEventListener('click', async () => {
                if (this.currentChannel) {
                    await this.toggleFavorite(this.currentChannel.id);
                }
            });
        }
        
        // Add playlist button
        const addPlaylistBtn = document.getElementById('add-playlist-btn');
        if (addPlaylistBtn) {
            addPlaylistBtn.addEventListener('click', () => {
                this.showAddPlaylistModal();
            });
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshCurrentView();
            });
        }
        
        // Recording buttons
        const recordBtn = document.getElementById('record-btn');
        if (recordBtn) {
            recordBtn.addEventListener('click', () => {
                if (this.activeRecordingId) {
                    this.stopRecording();
                } else {
                    this.showRecordingModal();
                }
            });
        }
        
        const recordingsBtn = document.getElementById('recordings-btn');
        if (recordingsBtn) {
            recordingsBtn.addEventListener('click', () => {
                this.showRecordingsListModal();
            });
        }
        
        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                if (!confirm('Are you sure you want to logout?')) return;
                
                try {
                    await fetch(`${API_BASE}/auth/logout`, {
                        method: 'POST',
                        credentials: 'include'
                    });
                    
                    window.location.href = '/login.html';
                } catch (error) {
                    console.error('Logout error:', error);
                    alert('Logout failed');
                }
            });
        }
        
        // Search
        const searchInput = document.getElementById('channel-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchChannels(e.target.value);
            });
        }
        
        // Modal
        const modalClose = document.getElementById('modal-close');
        if (modalClose) {
            modalClose.addEventListener('click', () => {
                this.hideModal();
            });
        }
        
        const modalOverlay = document.getElementById('modal-overlay');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target.id === 'modal-overlay') {
                    this.hideModal();
                }
            });
        }
        
        console.log('Event listeners setup complete');
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete') {
                e.preventDefault();
                if (this.selectedChannels.size > 0) {
                    this.deleteSelectedChannels();
                } else if (this.currentChannel) {
                    this.deleteChannel(this.currentChannel.id);
                }
            }
            
            if (e.ctrlKey && e.key === 'a') {
                e.preventDefault();
                this.selectAllChannels();
            }
            
            if (e.key === 'Escape') {
                this.clearSelection();
            }
            
            if (e.key === 'f' || e.key === 'F') {
                if (this.currentChannel) {
                    this.toggleFavorite(this.currentChannel.id);
                }
            }
        });
    }
    
    selectAllChannels() {
        this.selectedChannels.clear();
        this.channels.forEach(ch => this.selectedChannels.add(ch.id));
        this.updateChannelSelection();
        console.log(`Selected ${this.selectedChannels.size} channels`);
    }
    
    clearSelection() {
        this.selectedChannels.clear();
        this.updateChannelSelection();
    }
    
    updateChannelSelection() {
        document.querySelectorAll('.channel-item').forEach(item => {
            const channelId = parseInt(item.dataset.channelId);
            if (this.selectedChannels.has(channelId)) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });
    }
    
    async toggleFavorite(channelId) {
        try {
            const response = await fetch(`${API_BASE}/channels/${channelId}/favorite`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.status === 401) {
                alert('Session expired. Please login again.');
                window.location.href = '/login.html';
                return;
            }
            
            if (response.ok) {
                const data = await response.json();
                console.log('Favorite toggled:', data);
                
                // Update current channel if it's the one being toggled
                if (this.currentChannel && this.currentChannel.id === channelId) {
                    this.currentChannel.is_favorite = data.is_favorite;
                    this.updateFavoriteStar();
                }
                
                // Update in channels array
                const channel = this.channels.find(ch => ch.id === channelId);
                if (channel) {
                    channel.is_favorite = data.is_favorite;
                }
                
                // Refresh favorites tab if active
                const favoritesTab = document.querySelector('.tab[data-tab="favorites"]');
                if (favoritesTab && favoritesTab.classList.contains('active')) {
                    this.loadFavorites();
                }
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
            alert('Failed to toggle favorite');
        }
    }
    
    updateFavoriteStar() {
        const favoriteStar = document.getElementById('favorite-star');
        if (!favoriteStar) return;
        
        if (this.currentChannel) {
            favoriteStar.style.display = 'block';
            if (this.currentChannel.is_favorite) {
                favoriteStar.textContent = '★';
                favoriteStar.classList.add('is-favorite');
            } else {
                favoriteStar.textContent = '☆';
                favoriteStar.classList.remove('is-favorite');
            }
        } else {
            favoriteStar.style.display = 'none';
        }
    }
    
    async deleteChannel(channelId) {
        if (!confirm('Delete this channel?')) return;
        
        try {
            const response = await fetch(`${API_BASE}/channels/${channelId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.status === 401) {
                alert('Session expired. Please login again.');
                window.location.href = '/login.html';
                return;
            }
            
            if (response.ok) {
                console.log(`Channel ${channelId} deleted`);
                
                const currentIndex = this.channels.findIndex(ch => ch.id === channelId);
                const nextChannel = this.channels[currentIndex + 1] || this.channels[currentIndex - 1];
                
                await this.loadChannels(this.currentPlaylist);
                
                if (nextChannel) {
                    const nextElement = document.querySelector(`[data-channel-id="${nextChannel.id}"]`);
                    if (nextElement) {
                        this.playChannel(nextChannel, nextElement);
                    }
                }
            }
        } catch (error) {
            console.error('Error deleting channel:', error);
            alert('Failed to delete channel');
        }
    }
    
    async deleteSelectedChannels() {
        if (this.selectedChannels.size === 0) return;
        
        if (!confirm(`Delete ${this.selectedChannels.size} selected channels?`)) return;
        
        try {
            const response = await fetch(`${API_BASE}/channels/bulk-delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ channel_ids: Array.from(this.selectedChannels) })
            });
            
            if (response.status === 401) {
                alert('Session expired. Please login again.');
                window.location.href = '/login.html';
                return;
            }
            
            if (response.ok) {
                const result = await response.json();
                console.log(`Deleted ${result.count} channels`);
                this.selectedChannels.clear();
                await this.loadChannels(this.currentPlaylist);
            }
        } catch (error) {
            console.error('Error bulk deleting channels:', error);
            alert('Failed to delete channels');
        }
    }
    
    async deletePlaylist(playlistId) {
        if (!confirm('Delete this entire playlist?')) return;
        
        try {
            const response = await fetch(`${API_BASE}/playlists/${playlistId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.status === 401) {
                alert('Session expired. Please login again.');
                window.location.href = '/login.html';
                return;
            }
            
            if (response.ok) {
                console.log(`Playlist ${playlistId} deleted`);
                this.currentPlaylist = null;
                await this.loadPlaylists();
                document.getElementById('channel-list').innerHTML = '<div class="empty-state">Playlist deleted. Add a new one.</div>';
            }
        } catch (error) {
            console.error('Error deleting playlist:', error);
            alert('Failed to delete playlist');
        }
    }
    
    showRecordingModal() {
        if (!this.currentChannel) {
            alert('Please select a channel first');
            return;
        }
        
        const modal = document.getElementById('modal-overlay');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.textContent = `Record: ${this.currentChannel.name}`;
        
        modalBody.innerHTML = `
            <form id="recording-form">
                <div class="form-group">
                    <label>Recording Duration</label>
                    <select name="duration" id="recording-duration">
                        <option value="1800">30 minutes</option>
                        <option value="3600" selected>1 hour</option>
                        <option value="7200">2 hours</option>
                        <option value="10800">3 hours</option>
                        <option value="14400">4 hours</option>
                        <option value="21600">6 hours</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Channel</label>
                    <input type="text" value="${this.currentChannel.name}" readonly>
                </div>
                
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="app.hideModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">⏺ Start Recording</button>
                </div>
            </form>
        `;
        
        document.getElementById('recording-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const duration = parseInt(document.getElementById('recording-duration').value);
            await this.startRecording(duration);
        });
        
        modal.classList.remove('hidden');
    }
    
    async startRecording(duration) {
        if (!this.currentChannel) return;
        
        try {
            const response = await fetch(`${API_BASE}/recordings/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    stream_url: this.currentChannel.stream_url,
                    channel_name: this.currentChannel.name,
                    duration: duration
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.hideModal();
                alert(`Recording started!\nDuration: ${duration/60} minutes\nFile: ${result.filename}`);
                
                const recordBtn = document.getElementById('record-btn');
                recordBtn.classList.add('recording');
                recordBtn.textContent = '⏹ STOP REC';
                
                this.activeRecordingId = result.recording_id;
            } else {
                alert(`Failed to start recording: ${result.error}`);
            }
        } catch (error) {
            console.error('Recording error:', error);
            alert('Failed to start recording');
        }
    }
    
    async stopRecording() {
        if (!this.activeRecordingId) return;
        
        if (!confirm('Stop current recording?')) return;
        
        try {
            const response = await fetch(`${API_BASE}/recordings/stop/${this.activeRecordingId}`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                const recordBtn = document.getElementById('record-btn');
                recordBtn.classList.remove('recording');
                recordBtn.textContent = '⏺ RECORD';
                
                this.activeRecordingId = null;
                alert('Recording stopped');
            }
        } catch (error) {
            console.error('Stop recording error:', error);
        }
    }
    
    async showRecordingsListModal() {
        const modal = document.getElementById('modal-overlay');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.textContent = 'Recordings';
        modalBody.innerHTML = '<div class="loading">Loading recordings...</div>';
        modal.classList.remove('hidden');
        
        try {
            const response = await fetch(`${API_BASE}/recordings/list`, {
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.recordings.length === 0 && data.active.length === 0) {
                modalBody.innerHTML = '<div class="empty-state">No recordings yet</div>';
                return;
            }
            
            let html = '';
            
            if (data.active.length > 0) {
                html += '<h3 style="margin-bottom: 12px;">Active Recordings</h3><div class="recordings-list">';
                data.active.forEach(rec => {
                    html += `
                        <div class="recording-item active">
                            <div class="recording-info">
                                <div class="recording-name">⏺ ${rec.channel}</div>
                                <div class="recording-details">Started: ${new Date(rec.started_at).toLocaleString()}</div>
                            </div>
                            <button class="btn btn-secondary btn-sm" onclick="app.stopRecordingById('${rec.id}')">⏹ Stop</button>
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            if (data.recordings.length > 0) {
                html += '<h3 style="margin: 20px 0 12px 0;">Saved Recordings</h3><div class="recordings-list">';
                data.recordings.forEach(rec => {
                    html += `
                        <div class="recording-item">
                            <div class="recording-info">
                                <div class="recording-name">${rec.filename}</div>
                                <div class="recording-details">${rec.size_mb} MB • ${new Date(rec.created).toLocaleString()}</div>
                            </div>
                            <div class="recording-actions">
                                <a href="${API_BASE}/recordings/download/${rec.filename}" class="btn btn-primary btn-sm" download>⬇ Download</a>
                                <button class="btn btn-secondary btn-sm" onclick="app.deleteRecording('${rec.filename}')">🗑️ Delete</button>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            modalBody.innerHTML = html;
            
        } catch (error) {
            console.error('Error loading recordings:', error);
            modalBody.innerHTML = '<div class="error-state">Failed to load recordings</div>';
        }
    }
    
    async stopRecordingById(recordingId) {
        try {
            const response = await fetch(`${API_BASE}/recordings/stop/${recordingId}`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                alert('Recording stopped');
                this.showRecordingsListModal();
            }
        } catch (error) {
            console.error('Stop recording error:', error);
        }
    }
    
    async deleteRecording(filename) {
        if (!confirm(`Delete recording: ${filename}?`)) return;
        
        try {
            const response = await fetch(`${API_BASE}/recordings/delete/${filename}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
                this.showRecordingsListModal();
            } else {
                alert('Failed to delete recording');
            }
        } catch (error) {
            console.error('Delete recording error:', error);
            alert('Failed to delete recording');
        }
    }
    
    async refreshCurrentView() {
        console.log('Refreshing...');
        await this.loadPlaylists();
        if (this.currentPlaylist) {
            await this.loadChannels(this.currentPlaylist);
        }
        
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn.style.opacity = '0.5';
        setTimeout(() => { refreshBtn.style.opacity = '1'; }, 500);
    }
    
    async loadPlaylists() {
        try {
            const response = await fetch(`${API_BASE}/playlists`, {
                credentials: 'include'
            });
            
            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }
            
            this.playlists = await response.json();
            console.log(`Loaded ${this.playlists.length} playlists`);
            
            if (this.playlists.length > 0 && !this.currentPlaylist) {
                this.currentPlaylist = this.playlists[0].id;
                await this.loadChannels(this.playlists[0].id);
            }
        } catch (error) {
            console.error('Error loading playlists:', error);
        }
    }
    
    async loadChannels(playlistId, groupTitle = null) {
        try {
            let url = `${API_BASE}/channels?playlist_id=${playlistId}`;
            if (groupTitle) {
                url += `&group=${encodeURIComponent(groupTitle)}`;
            }
            
            const response = await fetch(url, {
                credentials: 'include'
            });
            
            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }
            
            this.channels = await response.json();
            console.log(`Loaded ${this.channels.length} channels`);
            this.renderChannels(this.channels);
            await this.loadGroups(playlistId);
        } catch (error) {
            console.error('Error loading channels:', error);
        }
    }
    
    renderChannels(channels) {
        const container = document.getElementById('channel-list');
        container.innerHTML = '';
        
        if (channels.length === 0) {
            container.innerHTML = '<div class="empty-state">No channels</div>';
            return;
        }
        
        channels.forEach((channel, index) => {
            const item = document.createElement('div');
            item.className = 'channel-item';
            item.dataset.channelId = channel.id;
            
            item.innerHTML = `
                <div class="channel-number">${index + 1}</div>
                ${channel.tvg_logo ? 
                    `<img src="${channel.tvg_logo}" class="channel-logo" onerror="this.style.display='none'">` : 
                    '<div class="channel-logo"></div>'}
                <div class="channel-name">${channel.name}</div>
                <button class="delete-channel-btn" title="Delete Channel">×</button>
            `;
            
            // Left click
            item.addEventListener('click', (e) => {
                if (e.target.classList.contains('delete-channel-btn')) {
                    return;
                }
                
                if (e.ctrlKey) {
                    if (this.selectedChannels.has(channel.id)) {
                        this.selectedChannels.delete(channel.id);
                    } else {
                        this.selectedChannels.add(channel.id);
                    }
                    this.updateChannelSelection();
                } else {
                    this.selectedChannels.clear();
                    this.playChannel(channel, item);
                }
            });
            
            // Right click context menu
            item.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.showContextMenu(e.pageX, e.pageY, channel);
            });
            
            item.querySelector('.delete-channel-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteChannel(channel.id);
            });
            
            container.appendChild(item);
        });
    }
    
    showContextMenu(x, y, channel) {
        this.contextMenuChannel = channel;
        const contextMenu = document.getElementById('context-menu');
        const contextFavorite = document.getElementById('context-favorite');
        const contextRemoveFavorite = document.getElementById('context-remove-favorite');
        
        if (channel.is_favorite) {
            contextFavorite.style.display = 'none';
            contextRemoveFavorite.style.display = 'block';
        } else {
            contextFavorite.style.display = 'block';
            contextRemoveFavorite.style.display = 'none';
        }
        
        contextMenu.style.left = `${x}px`;
        contextMenu.style.top = `${y}px`;
        contextMenu.classList.remove('hidden');
    }
    
    async loadGroups(playlistId) {
        try {
            const response = await fetch(`${API_BASE}/channels/groups?playlist_id=${playlistId}`, {
                credentials: 'include'
            });
            
            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }
            
            const groups = await response.json();
            this.renderGroups(groups);
        } catch (error) {
            console.error('Error loading groups:', error);
        }
    }
    
    renderGroups(groups) {
        const container = document.getElementById('group-list');
        container.innerHTML = '';
        
        if (groups.length === 0) {
            container.innerHTML = '<div class="empty-state">No groups</div>';
            return;
        }
        
        const allItem = document.createElement('div');
        allItem.className = 'group-item active';
        allItem.innerHTML = `
            📺 All Channels
            <button class="delete-playlist-btn" title="Delete Playlist">🗑️</button>
        `;
        allItem.querySelector('.delete-playlist-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.deletePlaylist(this.currentPlaylist);
        });
        allItem.addEventListener('click', () => {
            document.querySelectorAll('.group-item').forEach(g => g.classList.remove('active'));
            allItem.classList.add('active');
            this.loadChannels(this.currentPlaylist);
        });
        container.appendChild(allItem);
        
        groups.forEach(group => {
            const item = document.createElement('div');
            item.className = 'group-item';
            item.textContent = group;
            item.addEventListener('click', () => {
                document.querySelectorAll('.group-item').forEach(g => g.classList.remove('active'));
                item.classList.add('active');
                this.loadChannels(this.currentPlaylist, group);
            });
            container.appendChild(item);
        });
    }
    
    playChannel(channel, element) {
        console.log(`Playing: ${channel.name}`);
        this.currentChannel = channel;
        
        document.getElementById('current-channel-name').textContent = channel.name;
        document.getElementById('video-overlay').classList.add('hidden');
        
        // Update favorite star
        this.updateFavoriteStar();
        
        document.querySelectorAll('.channel-item').forEach(item => item.classList.remove('active'));
        if (element) element.classList.add('active');
        
        if (window.player) {
            window.player.loadStream(channel.stream_url);
        }
    }
    
    async loadFavorites() {
        try {
            const response = await fetch(`${API_BASE}/channels?favorites=true`, {
                credentials: 'include'
            });
            
            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }
            
            this.channels = await response.json();
            
            const container = document.getElementById('favorites-list');
            container.innerHTML = '';
            
            if (this.channels.length === 0) {
                container.innerHTML = '<div class="empty-state">No favorites yet</div>';
                return;
            }
            
            this.channels.forEach((channel, index) => {
                const item = document.createElement('div');
                item.className = 'channel-item';
                
                item.innerHTML = `
                    <div class="channel-number">${index + 1}</div>
                    ${channel.tvg_logo ? `<img src="${channel.tvg_logo}" class="channel-logo" onerror="this.style.display='none'">` : '<div class="channel-logo"></div>'}
                    <div class="channel-name">${channel.name}</div>
                `;
                
                item.addEventListener('click', () => this.playChannel(channel, item));
                
                // Right click on favorites
                item.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    this.showContextMenu(e.pageX, e.pageY, channel);
                });
                
                container.appendChild(item);
            });
        } catch (error) {
            console.error('Error loading favorites:', error);
        }
    }
    
    searchChannels(query) {
        if (!query) {
            this.renderChannels(this.channels);
            return;
        }
        
        const filtered = this.channels.filter(channel =>
            channel.name.toLowerCase().includes(query.toLowerCase()) ||
            (channel.tvg_name && channel.tvg_name.toLowerCase().includes(query.toLowerCase()))
        );
        
        this.renderChannels(filtered);
    }
    
    showAddPlaylistModal() {
        const modal = document.getElementById('modal-overlay');
        const modalBody = document.getElementById('modal-body');
        
        document.getElementById('modal-title').textContent = 'Add Playlist';
        
        modalBody.innerHTML = `
            <form id="add-playlist-form">
                <div class="form-group">
                    <label>Playlist Name</label>
                    <input type="text" name="name" required>
                </div>
                
                <div class="form-group">
                    <label>Playlist Type</label>
                    <select name="playlist_type" id="playlist-type">
                        <option value="m3u">M3U/M3U8</option>
                        <option value="xtream">Xtream Codes</option>
                        <option value="stalker">Stalker Portal</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Source Type</label>
                    <select name="source_type" id="source-type">
                        <option value="url">URL</option>
                        <option value="file">Upload File</option>
                    </select>
                </div>
                
                <div class="form-group" id="url-group">
                    <label>URL</label>
                    <input type="url" name="source_url">
                </div>
                
                <div class="form-group hidden" id="file-group">
                    <label>File</label>
                    <input type="file" name="file" accept=".m3u,.m3u8">
                </div>
                
                <div class="form-group hidden" id="xtream-group">
                    <label>Username</label>
                    <input type="text" name="xtream_username">
                    <label>Password</label>
                    <input type="password" name="xtream_password">
                </div>
                
                <div class="form-group hidden" id="stalker-group">
                    <label>MAC Address</label>
                    <input type="text" name="stalker_mac" placeholder="00:1A:79:XX:XX:XX">
                </div>
                
                <div class="form-group">
                    <label>User Agent (Optional)</label>
                    <input type="text" name="user_agent">
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="auto_update" checked>
                        Auto-update on startup
                    </label>
                </div>
                
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="app.hideModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Playlist</button>
                </div>
            </form>
        `;
        
        document.getElementById('playlist-type').addEventListener('change', (e) => {
            this.updatePlaylistForm(e.target.value);
        });
        
        document.getElementById('source-type').addEventListener('change', (e) => {
            this.updateSourceForm(e.target.value);
        });
        
        document.getElementById('add-playlist-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitPlaylist(e.target);
        });
        
        modal.classList.remove('hidden');
    }
    
    updatePlaylistForm(type) {
        document.getElementById('xtream-group').classList.add('hidden');
        document.getElementById('stalker-group').classList.add('hidden');
        
        if (type === 'xtream') {
            document.getElementById('xtream-group').classList.remove('hidden');
        } else if (type === 'stalker') {
            document.getElementById('stalker-group').classList.remove('hidden');
        }
    }
    
    updateSourceForm(type) {
        document.getElementById('url-group').classList.toggle('hidden', type === 'file');
        document.getElementById('file-group').classList.toggle('hidden', type === 'url');
    }
    
    async submitPlaylist(form) {
        const formData = new FormData(form);
        const sourceType = formData.get('source_type');
        
        const data = {
            name: formData.get('name'),
            playlist_type: formData.get('playlist_type'),
            source_type: sourceType,
            auto_update: formData.get('auto_update') === 'on',
            user_agent: formData.get('user_agent') || null,
            xtream_username: formData.get('xtream_username') || null,
            xtream_password: formData.get('xtream_password') || null,
            stalker_mac: formData.get('stalker_mac') || null
        };
        
        try {
            if (sourceType === 'file') {
                const fileInput = form.querySelector('input[name="file"]');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Please select a file');
                    return;
                }
                
                const uploadFormData = new FormData();
                uploadFormData.append('file', file);
                
                const uploadResponse = await fetch(`${API_BASE}/playlists/upload`, {
                    method: 'POST',
                    credentials: 'include',
                    body: uploadFormData
                });
                
                if (!uploadResponse.ok) {
                    const error = await uploadResponse.json();
                    alert(error.error || 'File upload failed');
                    return;
                }
                
                const uploadResult = await uploadResponse.json();
                data.file_path = uploadResult.filepath;
                
            } else {
                data.source_url = formData.get('source_url');
            }
            
            const response = await fetch(`${API_BASE}/playlists`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.hideModal();
                alert(`Playlist "${result.name}" added with ${result.channel_count} channels!`);
                await this.loadPlaylists();
                this.currentPlaylist = result.id;
                await this.loadChannels(result.id);
            } else {
                alert(result.error || 'Failed to add playlist');
            }
        } catch (error) {
            console.error('Error adding playlist:', error);
            alert('Error: ' + error.message);
        }
    }
    
    hideModal() {
        document.getElementById('modal-overlay').classList.add('hidden');
    }
}

// Initialize app
const app = new IPTVApp();
