export class WebSocketManager {
    constructor() {
        this.ws = null;
        this.onStatusUpdate = null;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.showNotification('Connected to server', 'info');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (this.onStatusUpdate) {
                this.onStatusUpdate(data);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected, attempting reconnect...');
            setTimeout(() => this.connect(), 1000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showNotification('Connection error, retrying...', 'error');
        };
    }

    showNotification(message, type) {
        // Emit a custom event for notifications
        const event = new CustomEvent('notification', {
            detail: { message, type }
        });
        document.dispatchEvent(event);
    }

    setStatusUpdateHandler(handler) {
        this.onStatusUpdate = handler;
    }
}