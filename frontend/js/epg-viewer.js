class EPGViewer {
    constructor() {
        this.currentChannel = null;
        this.programmes = [];
    }
    
    async loadProgrammes(channelId) {
        this.currentChannel = channelId;
        
        try {
            const response = await fetch(`/api/epg/programmes?channel_id=${encodeURIComponent(channelId)}`);
            this.programmes = await response.json();
            this.render();
        } catch (error) {
            console.error('Error loading EPG:', error);
            this.showPlaceholder();
        }
    }
    
    async loadCurrent(channelId) {
        try {
            const response = await fetch(`/api/epg/current?channel_id=${encodeURIComponent(channelId)}`);
            const programme = await response.json();
            this.displayCurrent(programme);
        } catch (error) {
            console.error('Error loading current programme:', error);
        }
    }
    
    render() {
        const container = document.getElementById('epg-container');
        
        if (!this.programmes || this.programmes.length === 0) {
            this.showPlaceholder();
            return;
        }
        
        const now = new Date();
        container.innerHTML = '';
        
        this.programmes.forEach(prog => {
            const start = new Date(prog.start);
            const stop = new Date(prog.stop);
            const isCurrent = start <= now && now <= stop;
            
            const div = document.createElement('div');
            div.className = `epg-programme ${isCurrent ? 'current' : ''}`;
            div.innerHTML = `
                <div class="epg-time">
                    ${start.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} - 
                    ${stop.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                </div>
                <div class="epg-title">${prog.title}</div>
                ${prog.desc ? `<div class="epg-desc">${prog.desc}</div>` : ''}
            `;
            container.appendChild(div);
        });
    }
    
    displayCurrent(programme) {
        const info = document.getElementById('epg-info');
        
        if (!programme) {
            info.innerHTML = '<p>No EPG information available</p>';
            return;
        }
        
        const start = new Date(programme.start);
        const stop = new Date(programme.stop);
        
        info.innerHTML = `
            <div>
                <strong>${programme.title}</strong>
                <br>
                ${start.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} - 
                ${stop.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </div>
            ${programme.desc ? `<p>${programme.desc}</p>` : ''}
        `;
    }
    
    showPlaceholder() {
        const container = document.getElementById('epg-container');
        container.innerHTML = '<p class="epg-placeholder">No TV guide available for this channel</p>';
    }
}

const epgViewer = new EPGViewer();
window.epgViewer = epgViewer;
