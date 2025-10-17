import requests

class XtreamParser:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.player_api_url = f"{self.base_url}/player_api.php"
    
    def get_live_streams(self):
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_live_streams'
        }
        
        response = requests.get(self.player_api_url, params=params, timeout=30)
        response.raise_for_status()
        streams = response.json()
        
        channels = []
        for stream in streams:
            channel = {
                'name': stream.get('name', ''),
                'stream_id': stream.get('stream_id'),
                'stream_url': f"{self.base_url}/live/{self.username}/{self.password}/{stream.get('stream_id')}.m3u8",
                'tvg_id': stream.get('epg_channel_id', ''),
                'tvg_name': stream.get('name', ''),
                'tvg_logo': stream.get('stream_icon', ''),
                'group_title': stream.get('category_name', ''),
                'catchup': 'default' if stream.get('tv_archive') == 1 else '',
                'catchup_days': stream.get('tv_archive_duration', 0)
            }
            channels.append(channel)
        
        return channels
    
    def get_vod_streams(self):
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_vod_streams'
        }
        
        response = requests.get(self.player_api_url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_series(self):
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_series'
        }
        
        response = requests.get(self.player_api_url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_epg(self, stream_id):
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_short_epg',
            'stream_id': stream_id
        }
        
        response = requests.get(self.player_api_url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
