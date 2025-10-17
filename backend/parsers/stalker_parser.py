import requests
import hashlib
import time
import random

class StalkerParser:
    def __init__(self, portal_url, mac_address):
        self.portal_url = portal_url.rstrip('/')
        self.mac_address = mac_address
        self.token = None
    
    def _get_token(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
            'X-User-Agent': 'Model: MAG250; Link: WiFi',
            'Cookie': f'mac={self.mac_address}; stb_lang=en; timezone=Europe/London'
        }
        
        url = f"{self.portal_url}/portal.php?type=stb&action=handshake&token=&JsHttpRequest=1-xml"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        self.token = data.get('js', {}).get('token', '')
        return self.token
    
    def get_genres(self):
        if not self.token:
            self._get_token()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'mac={self.mac_address}'
        }
        
        url = f"{self.portal_url}/portal.php?type=itv&action=get_genres&JsHttpRequest=1-xml"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def get_channels(self, genre='*'):
        if not self.token:
            self._get_token()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'mac={self.mac_address}'
        }
        
        url = f"{self.portal_url}/portal.php?type=itv&action=get_all_channels&genre={genre}&JsHttpRequest=1-xml"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        channels = []
        
        for ch in data.get('js', {}).get('data', []):
            channel = {
                'name': ch.get('name', ''),
                'stream_url': ch.get('cmd', ''),
                'tvg_id': ch.get('id', ''),
                'tvg_logo': ch.get('logo', ''),
                'group_title': genre if genre != '*' else '',
                'channel_number': ch.get('number', 0)
            }
            channels.append(channel)
        
        return channels
    
    def create_link(self, cmd):
        if not self.token:
            self._get_token()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'mac={self.mac_address}'
        }
        
        url = f"{self.portal_url}/portal.php?type=itv&action=create_link&cmd={cmd}&JsHttpRequest=1-xml"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get('js', {}).get('cmd', '')
