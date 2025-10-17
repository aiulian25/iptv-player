import xml.etree.ElementTree as ET
from datetime import datetime
import requests

class XMLTVParser:
    def __init__(self):
        self.channels = {}
        self.programmes = []
    
    def parse(self, content):
        root = ET.fromstring(content)
        
        for channel in root.findall('channel'):
            channel_id = channel.get('id')
            display_name = channel.find('display-name')
            icon = channel.find('icon')
            
            self.channels[channel_id] = {
                'id': channel_id,
                'display_name': display_name.text if display_name is not None else '',
                'icon': icon.get('src') if icon is not None else ''
            }
        
        for programme in root.findall('programme'):
            prog_data = {
                'channel': programme.get('channel'),
                'start': self._parse_time(programme.get('start')),
                'stop': self._parse_time(programme.get('stop')),
                'title': '',
                'desc': '',
                'category': '',
                'icon': ''
            }
            
            title = programme.find('title')
            if title is not None:
                prog_data['title'] = title.text
            
            desc = programme.find('desc')
            if desc is not None:
                prog_data['desc'] = desc.text
            
            category = programme.find('category')
            if category is not None:
                prog_data['category'] = category.text
            
            icon = programme.find('icon')
            if icon is not None:
                prog_data['icon'] = icon.get('src')
            
            self.programmes.append(prog_data)
        
        return {
            'channels': self.channels,
            'programmes': self.programmes
        }
    
    def _parse_time(self, time_str):
        if not time_str:
            return None
        
        try:
            return datetime.strptime(time_str[:14], '%Y%m%d%H%M%S')
        except:
            return None
    
    def parse_from_url(self, url):
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return self.parse(response.content)
    
    def parse_from_file(self, file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        return self.parse(content)
    
    def get_current_programme(self, channel_id):
        now = datetime.utcnow()
        for prog in self.programmes:
            if prog['channel'] == channel_id:
                if prog['start'] <= now <= prog['stop']:
                    return prog
        return None
    
    def get_programmes_by_channel(self, channel_id, start_time=None, end_time=None):
        results = []
        for prog in self.programmes:
            if prog['channel'] == channel_id:
                if start_time and prog['stop'] < start_time:
                    continue
                if end_time and prog['start'] > end_time:
                    continue
                results.append(prog)
        return sorted(results, key=lambda x: x['start'])
