from flask import Blueprint, request, Response, jsonify
import requests
from urllib.parse import urlparse, urljoin
import re

stream_bp = Blueprint("stream", __name__)

@stream_bp.route("/manifest", methods=["GET"])
def stream_manifest():
    """
    Fetch M3U8 manifest and rewrite URLs to point to our proxy.
    """
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL parameter required"}), 400
    
    print(f"[MANIFEST] Fetching: {url}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": urlparse(url).scheme + "://" + urlparse(url).netloc + "/",
            "Accept": "*/*",
        }
        
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        content = resp.text
        print(f"[MANIFEST] Received {len(content)} bytes")
        
        # Get base URL for relative paths
        base_url = url.rsplit('/', 1)[0] + '/'
        
        # Rewrite URLs in the manifest
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if line.startswith('#') or not line:
                new_lines.append(line)
                continue
            
            # This is a URL line
            if line.startswith('http://') or line.startswith('https://'):
                # Already absolute URL
                absolute_url = line
            else:
                # Relative URL - make it absolute
                absolute_url = urljoin(base_url, line)
            
            # Rewrite to go through our segment proxy
            proxied_url = f"/hls-proxy/segment?url={requests.utils.quote(absolute_url, safe='')}"
            new_lines.append(proxied_url)
            print(f"[MANIFEST] Rewrite: {line} -> {proxied_url}")
        
        rewritten_content = '\n'.join(new_lines)
        
        response = Response(rewritten_content, mimetype='application/vnd.apple.mpegurl')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Cache-Control'] = 'no-cache'
        
        print(f"[MANIFEST] Returning rewritten manifest")
        return response
        
    except Exception as e:
        print(f"[MANIFEST] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@stream_bp.route("/segment", methods=["GET"])
def stream_segment():
    """
    Proxy video segments (.ts files) and sub-manifests (.m3u8).
    """
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL parameter required"}), 400
    
    print(f"[SEGMENT] Fetching: {url}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": urlparse(url).scheme + "://" + urlparse(url).netloc + "/",
            "Accept": "*/*",
        }
        
        # Add Range header if present
        if request.headers.get('Range'):
            headers['Range'] = request.headers.get('Range')
        
        resp = requests.get(url, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()
        
        print(f"[SEGMENT] Got response: {resp.status_code}, Content-Type: {resp.headers.get('Content-Type')}")
        
        # Check if this is another manifest (nested m3u8)
        content_type = resp.headers.get('Content-Type', '')
        if 'mpegurl' in content_type or url.endswith('.m3u8'):
            # This is a nested manifest, rewrite it too
            content = resp.text
            base_url = url.rsplit('/', 1)[0] + '/'
            
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('#') or not line:
                    new_lines.append(line)
                    continue
                
                if line.startswith('http://') or line.startswith('https://'):
                    absolute_url = line
                else:
                    absolute_url = urljoin(base_url, line)
                
                proxied_url = f"/hls-proxy/segment?url={requests.utils.quote(absolute_url, safe='')}"
                new_lines.append(proxied_url)
            
            rewritten_content = '\n'.join(new_lines)
            response = Response(rewritten_content, mimetype='application/vnd.apple.mpegurl')
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Cache-Control'] = 'no-cache'
            return response
        
        # Regular segment - stream it
        def generate():
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        response = Response(generate(), status=resp.status_code)
        
        # Copy headers
        for header in ['Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges']:
            if header in resp.headers:
                response.headers[header] = resp.headers[header]
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        
        print(f"[SEGMENT] Streaming segment")
        return response
        
    except Exception as e:
        print(f"[SEGMENT] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
