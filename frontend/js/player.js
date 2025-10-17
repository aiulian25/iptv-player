class VideoPlayer {
    constructor() {
        this.video = document.getElementById('video-player');
        this.hls = null;
        this.currentUrl = null;
    }
    
    loadStream(url) {
        this.currentUrl = url;
        
        console.log(`Loading stream: ${url}`);
        
        // Clean up existing player
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }
        
        // Always use proxy to bypass CORS
        const proxyUrl = `/hls-proxy/manifest?url=${encodeURIComponent(url)}`;
        console.log(`Using proxy: ${proxyUrl}`);
        
        if (Hls.isSupported()) {
            this.hls = new Hls({
                debug: false,
                enableWorker: true,
                lowLatencyMode: false,
                backBufferLength: 90,
                maxBufferLength: 30,
                maxMaxBufferLength: 600,
                xhrSetup: function(xhr) {
                    xhr.withCredentials = false;
                }
            });
            
            this.hls.loadSource(proxyUrl);
            this.hls.attachMedia(this.video);
            
            this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
                console.log('✓ Stream manifest loaded successfully');
                document.getElementById('video-overlay').classList.add('hidden');
                this.video.play().catch(e => {
                    console.log('Autoplay prevented, user interaction needed');
                });
            });
            
            this.hls.on(Hls.Events.FRAG_LOADED, (event, data) => {
                console.log(`✓ Loaded fragment: ${data.frag.sn}`);
            });
            
            this.hls.on(Hls.Events.ERROR, (event, data) => {
                if (data.fatal) {
                    console.error('Fatal HLS error:', data);
                    
                    switch(data.type) {
                        case Hls.ErrorTypes.NETWORK_ERROR:
                            console.log('Network error, attempting recovery...');
                            this.showError('Network error. Retrying...');
                            setTimeout(() => {
                                if (this.hls) {
                                    this.hls.startLoad();
                                }
                            }, 2000);
                            break;
                            
                        case Hls.ErrorTypes.MEDIA_ERROR:
                            console.log('Media error, attempting recovery...');
                            this.hls.recoverMediaError();
                            break;
                            
                        default:
                            console.error('Unrecoverable error');
                            this.showError('Stream failed. Channel may be offline or geo-blocked.');
                            break;
                    }
                } else {
                    console.warn('Non-fatal HLS error:', data);
                }
            });
            
        } else if (this.video.canPlayType('application/vnd.apple.mpegurl')) {
            // Native HLS support (Safari)
            this.video.src = proxyUrl;
            this.video.addEventListener('loadedmetadata', () => {
                document.getElementById('video-overlay').classList.add('hidden');
                this.video.play();
            });
        } else {
            this.showError('HLS not supported. Please use Chrome, Firefox, or Safari.');
        }
    }
    
    showError(message) {
        const overlay = document.getElementById('video-overlay');
        const overlayText = overlay.querySelector('.overlay-text');
        
        if (overlayText) {
            overlayText.textContent = message;
            overlay.classList.remove('hidden');
        }
    }
    
    stop() {
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }
        this.video.pause();
        this.video.src = '';
    }
}

const player = new VideoPlayer();
window.player = player;
