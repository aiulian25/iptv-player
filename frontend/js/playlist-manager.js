class PlaylistManager {
    constructor() {
        this.playlists = [];
    }
    
    async importFromUrl(url, name, type, userAgent = null) {
        const data = {
            name: name,
            source_type: 'url',
            source_url: url,
            playlist_type: type,
            user_agent: userAgent,
            auto_update: true
        };
        
        return await this.addPlaylist(data);
    }
    
    async importFromFile(file, name, type) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/playlists/upload', {
            method: 'POST',
            body: formData
        });
        
        const fileData = await response.json();
        
        const data = {
            name: name,
            source_type: 'file',
            file_path: fileData.filepath,
            playlist_type: type,
            auto_update: false
        };
        
        return await this.addPlaylist(data);
    }
    
    async addPlaylist(data) {
        const response = await fetch('/api/playlists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to add playlist');
        }
        
        return await response.json();
    }
    
    async deletePlaylist(playlistId) {
        const response = await fetch(`/api/playlists/${playlistId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete playlist');
        }
        
        return await response.json();
    }
}

const playlistManager = new PlaylistManager();
window.playlistManager = playlistManager;
