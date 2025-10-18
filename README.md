# IPTV Player

A modern, feature-rich web-based IPTV player with user authentication, playlist management, and recording capabilities.


## Features

### Media Player
- **HLS.js** powered video streaming
- Live TV playback with adaptive bitrate
- Channel browsing with logos and grouping
- Search functionality
- Favorites system with right-click context menu

### User Management
- Secure authentication system
- Admin and regular user roles
- Multi-user support with individual preferences
- Password change enforcement on first login

### Playlist Management
- **M3U/M3U8** playlist support
- **Xtream Codes API** integration
- **Stalker Portal** support
- Upload local playlist files
- URL-based playlist import
- Auto-update playlists on startup
- Group and organize channels
- Bulk channel deletion

### Recording
- Record live streams
- Configurable recording duration (30 min to 6 hours)
- Download recorded content
- Active recording management

### User Interface
- **Dark/Light theme** toggle
- Responsive design
- Clean, modern interface
- Real-time channel switching
- Context menus for quick actions

### Settings
- Change username and password
- Store M3U files for backup
- User management (admin only)
- Theme customization

## Screenshots

<p align="center">
  <img src="screenshots/login.png" alt="Login Page" width="45%" />
  <img src="screenshots/player.png" alt="Channel Browser" width="45%" />
</p>

<p align="center">
  <img src="screenshots/settings.png" alt="Settings Page" width="45%" />


##  Quick Start

-For new machines, use the pre-built image from Docker Hub: image: aiulian25/iptv-player:latest


### Prerequisites
- Docker
- Docker Compose

### Installation

1. **Clone the repository:**
# iptv-player
