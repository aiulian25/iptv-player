from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import requests
import re

Base = declarative_base()

class Playlist(Base):
    __tablename__ = 'playlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    playlist_type = Column(String(50), default='m3u')
    source_type = Column(String(50), default='url')
    source_url = Column(Text)
    file_path = Column(Text)
    user_agent = Column(String(255))
    xtream_username = Column(String(255))
    xtream_password = Column(String(255))
    stalker_mac = Column(String(255))
    auto_update = Column(Boolean, default=True)
    channel_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime)
    
    channels = relationship("Channel", back_populates="playlist", cascade="all, delete-orphan")

class Channel(Base):
    __tablename__ = 'channels'
    
    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey('playlists.id'), nullable=False)
    name = Column(String(255), nullable=False)
    group_title = Column(String(255))
    tvg_id = Column(String(255))
    tvg_name = Column(String(255))
    tvg_logo = Column(Text)
    stream_url = Column(Text, nullable=False)
    catchup = Column(String(50))
    catchup_source = Column(Text)
    catchup_days = Column(Integer)
    is_favorite = Column(Boolean, default=False)
    channel_number = Column(Integer)
    
    playlist = relationship("Playlist", back_populates="channels")

class EPGSource(Base):
    __tablename__ = 'epg_sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    last_updated = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

# Global engine and session
_engine = None
_SessionLocal = None

def init_db(db_path: str):
    """Initialize database with all tables"""
    global _engine, _SessionLocal
    
    _engine = create_engine(f"sqlite:///{db_path}")
    _SessionLocal = sessionmaker(bind=_engine)
    
    # Create all tables
    Base.metadata.create_all(_engine)
    
    # Import User model and create its table
    try:
        from models.user import User, Base as UserBase
        UserBase.metadata.create_all(_engine)
        
        # Create default admin user if doesn't exist
        session = _SessionLocal()
        try:
            admin_user = session.query(User).filter_by(username='admin').first()
            if not admin_user:
                admin = User(
                    username='admin',
                    is_admin=True,
                    must_change_password=True
                )
                admin.set_password('admin123')
                session.add(admin)
                session.commit()
                print("✓ Default admin user created (username: admin, password: admin123)")
                print("⚠ IMPORTANT: Change the default password on first login!")
        except Exception as e:
            print(f"Error creating default admin: {e}")
            session.rollback()
        finally:
            session.close()
    except ImportError:
        print("User model not found, skipping user creation")
    
    return _engine

def get_session():
    """Get database session"""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _SessionLocal()

def parse_m3u(content: str):
    """Parse M3U/M3U8 content"""
    channels = []
    lines = content.split('\n')
    
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('#EXTINF:'):
            # Parse EXTINF line
            current_channel = {}
            
            # Extract attributes
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
            tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            group_match = re.search(r'group-title="([^"]*)"', line)
            
            if tvg_id_match:
                current_channel['tvg_id'] = tvg_id_match.group(1)
            if tvg_name_match:
                current_channel['tvg_name'] = tvg_name_match.group(1)
            if tvg_logo_match:
                current_channel['tvg_logo'] = tvg_logo_match.group(1)
            if group_match:
                current_channel['group_title'] = group_match.group(1)
            
            # Extract channel name (after last comma)
            name_part = line.split(',', 1)
            if len(name_part) > 1:
                current_channel['name'] = name_part[1].strip()
            
        elif line and not line.startswith('#') and current_channel:
            # This is the stream URL
            current_channel['stream_url'] = line
            channels.append(current_channel)
            current_channel = {}
    
    return channels

def add_playlist(name, playlist_type, source_type, source_url=None, file_path=None, 
                user_agent=None, xtream_username=None, xtream_password=None, 
                stalker_mac=None, auto_update=True):
    """Add a new playlist"""
    session = get_session()
    
    try:
        playlist = Playlist(
            name=name,
            playlist_type=playlist_type,
            source_type=source_type,
            source_url=source_url,
            file_path=file_path,
            user_agent=user_agent,
            xtream_username=xtream_username,
            xtream_password=xtream_password,
            stalker_mac=stalker_mac,
            auto_update=auto_update
        )
        
        session.add(playlist)
        session.commit()
        session.refresh(playlist)
        
        # Load channels
        update_playlist_channels(playlist)
        
        return playlist
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def delete_playlist_by_id(playlist_id: int):
    """Delete a playlist by ID"""
    session = get_session()
    
    try:
        playlist = session.query(Playlist).get(playlist_id)
        if not playlist:
            return False
        
        session.delete(playlist)
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def update_playlist_channels(playlist):
    """Update channels for a playlist"""
    session = get_session()
    
    try:
        # Get playlist content
        if playlist.source_type == 'url' and playlist.source_url:
            headers = {}
            if playlist.user_agent:
                headers['User-Agent'] = playlist.user_agent
            
            response = requests.get(playlist.source_url, headers=headers, timeout=30)
            content = response.text
            
        elif playlist.source_type == 'file' and playlist.file_path:
            with open(playlist.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            raise ValueError("No valid source for playlist")
        
        # Parse channels
        parsed_channels = parse_m3u(content)
        
        # Delete old channels
        session.query(Channel).filter_by(playlist_id=playlist.id).delete()
        
        # Add new channels
        for idx, ch_data in enumerate(parsed_channels, start=1):
            channel = Channel(
                playlist_id=playlist.id,
                name=ch_data.get('name', 'Unknown'),
                group_title=ch_data.get('group_title'),
                tvg_id=ch_data.get('tvg_id'),
                tvg_name=ch_data.get('tvg_name'),
                tvg_logo=ch_data.get('tvg_logo'),
                stream_url=ch_data.get('stream_url', ''),
                channel_number=idx
            )
            session.add(channel)
        
        # Update playlist
        playlist.channel_count = len(parsed_channels)
        playlist.last_updated = datetime.utcnow()
        
        session.commit()
        
        print(f"Updated playlist '{playlist.name}' with {len(parsed_channels)} channels")
        
    except Exception as e:
        session.rollback()
        print(f"Error updating playlist channels: {e}")
        raise e
    finally:
        session.close()

def update_all_playlists(config):
    """Update all playlists that have auto_update enabled"""
    session = get_session()
    
    try:
        playlists = session.query(Playlist).filter_by(auto_update=True).all()
        
        for playlist in playlists:
            try:
                print(f"Auto-updating playlist: {playlist.name}")
                update_playlist_channels(playlist)
            except Exception as e:
                print(f"Failed to update playlist {playlist.name}: {e}")
        
    finally:
        session.close()
