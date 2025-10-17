import re
import requests
from urllib.parse import urljoin

class M3UParser:
    def __init__(self, user_agent=None):
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    def parse(self, content):
        """Parse M3U content and return list of channel dictionaries"""
        channels = []
        
        if not content or not content.strip():
            print("ERROR: Empty content provided to parser")
            return channels
        
        lines = content.strip().split('\n')
        print(f"Parsing M3U file with {len(lines)} lines")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments that aren't EXTINF
            if not line or (line.startswith('#') and not line.startswith('#EXTINF')):
                i += 1
                continue
            
            if line.startswith('#EXTINF'):
                try:
                    channel = self._parse_extinf_line(line)
                    
                    # Move to next non-comment line to get the URL
                    i += 1
                    while i < len(lines):
                        url_line = lines[i].strip()
                        if url_line and not url_line.startswith('#'):
                            channel['stream_url'] = url_line
                            if channel.get('name') and channel.get('stream_url'):
                                channels.append(channel)
                                print(f"Parsed channel: {channel['name']}")
                            else:
                                print(f"Skipped incomplete channel: {channel}")
                            break
                        i += 1
                except Exception as e:
                    print(f"Error parsing line {i}: {line[:100]} - {e}")
                    
            i += 1
        
        print(f"Total channels parsed: {len(channels)}")
        return channels
    
    def _parse_extinf_line(self, line):
        """Parse a single #EXTINF line and extract metadata"""
        channel = {
            'name': '',
            'tvg_id': '',
            'tvg_name': '',
            'tvg_logo': '',
            'group_title': '',
            'catchup': '',
            'catchup_source': '',
            'catchup_days': 0
        }
        
        # Define patterns for common M3U attributes
        patterns = {
            'tvg-id': r'tvg-id="([^"]*)"',
            'tvg-name': r'tvg-name="([^"]*)"',
            'tvg-logo': r'tvg-logo="([^"]*)"',
            'group-title': r'group-title="([^"]*)"',
            'catchup': r'catchup="([^"]*)"',
            'catchup-source': r'catchup-source="([^"]*)"',
            'catchup-days': r'catchup-days="([^"]*)"'
        }
        
        # Extract attributes
        for key, pattern in patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                field_name = key.replace('-', '_')
                channel[field_name] = match.group(1)
        
        # Extract channel name (everything after the last comma)
        # Format: #EXTINF:-1 tvg-id="..." tvg-name="..." ...,Channel Name
        name_match = re.search(r',([^,]+)$', line)
        if name_match:
            channel['name'] = name_match.group(1).strip()
        else:
            # Fallback: try to get anything after EXTINF:-1 or EXTINF:0
            fallback = re.search(r'#EXTINF:[^,]*,(.+)$', line)
            if fallback:
                channel['name'] = fallback.group(1).strip()
        
        # Convert catchup_days to integer
        if channel['catchup_days']:
            try:
                channel['catchup_days'] = int(channel['catchup_days'])
            except (ValueError, TypeError):
                channel['catchup_days'] = 0
        
        return channel
    
    def parse_from_url(self, url):
        """Download and parse M3U from URL"""
        print(f"Downloading M3U from: {url}")
        headers = {'User-Agent': self.user_agent}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return self.parse(response.text)
    
    def parse_from_file(self, file_path):
        """Parse M3U file with encoding tolerance"""
        print(f"Reading M3U file: {file_path}")
        
        # Try multiple encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Successfully read file with {encoding} encoding")
                break
            except (UnicodeDecodeError, FileNotFoundError) as e:
                print(f"Failed to read with {encoding}: {e}")
                continue
        
        if content is None:
            raise ValueError(f"Could not read file {file_path} with any supported encoding")
        
        return self.parse(content)
