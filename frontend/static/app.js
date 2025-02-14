import { WebSocketManager } from './js/modules/websocket.js';
import { UIManager } from './js/modules/ui.js';
import { FileHandler } from './js/modules/file-handler.js';
import { ModalManager } from './js/modules/modal.js';
import { ResultsHandler } from './js/modules/results-handler.js';

class App {
    constructor() {
        this.initializeElements();
        this.initializeManagers();
        this.setupEventListeners();
        this.loadInitialState();
    }

    initializeElements() {
        this.elements = {
            dropZone: document.getElementById('drop-zone'),
            previewGrid: document.getElementById('preview-grid'),
            categoriesInput: document.getElementById('categories-input'),
            startButton: document.getElementById('start-process'),
            processingSection: document.getElementById('processing-section'),
            resultsSection: document.getElementById('results-section'),
            statusText: document.getElementById('status-text'),
            resultsGrid: document.getElementById('results-grid'),
            downloadButton: document.getElementById('download-button'),
            clearButton: document.getElementById('clear-button'),
            clearSelectionButton: document.getElementById('clear-selection')
        };
    }

    initializeManagers() {
        // Initialize all managers
        this.websocket = new WebSocketManager();
        this.fileHandler = new FileHandler(this.elements.previewGrid);
        this.modalManager = new ModalManager();
        this.resultsHandler = new ResultsHandler(
            this.elements.resultsSection,
            this.elements.resultsGrid,
            this.elements.processingSection,
            this.elements.statusText
        );

        // Set up WebSocket status handler
        this.websocket.setStatusUpdateHandler(data => this.resultsHandler.updateStatus(data));
    }

    setupEventListeners() {
        // Drag and drop
        this.elements.dropZone.ondragover = e => {
            e.preventDefault();
            this.elements.dropZone.classList.add('dragover');
        };
        
        this.elements.dropZone.ondragleave = () => {
            this.elements.dropZone.classList.remove('dragover');
        };
        
        this.elements.dropZone.ondrop = e => {
            e.preventDefault();
            this.elements.dropZone.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        };

        // Browse button
        document.getElementById('browse-button').onclick = () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.accept = 'image/*';
            input.onchange = e => this.handleFiles(e.target.files);
            input.click();
        };

        // Categories input
        this.elements.categoriesInput.oninput = () => this.updateStartButton();

        // Start processing
        this.elements.startButton.onclick = () => this.startProcessing();

        // Clear buttons
        this.elements.clearButton.onclick = () => this.clearAll();
        this.elements.clearSelectionButton.onclick = () => this.clearSelection();

        // Download button
        this.elements.downloadButton.onclick = () => this.downloadResults();

        // Cleanup on page unload
        window.addEventListener('beforeunload', (e) => this.handleBeforeUnload(e));
    }

    async loadInitialState() {
        this.websocket.connect();
        const filesCount = await this.fileHandler.loadExistingPhotos();
        this.updateStartButton();
    }

    updateStartButton() {
        UIManager.updateStartButton(
            this.fileHandler.uploadedFiles,
            this.elements.categoriesInput,
            this.elements.startButton
        );
    }

    async handleFiles(files) {
        const filesCount = await this.fileHandler.handleFiles(files);
        this.updateStartButton();
    }

    async startProcessing() {
        const categories = this.elements.categoriesInput.value
            .split('\n')
            .map(cat => cat.trim())
            .filter(cat => cat);

        if (categories.length === 0) return;
        await this.resultsHandler.startProcessing(categories);
    }

    async clearAll() {
        if (this.resultsHandler.isProcessing()) {
            UIManager.showNotification('Cannot clear while processing', 'info');
            return;
        }

        try {
            await fetch('/clear', { method: 'POST' });
            this.fileHandler.clear();
            this.elements.categoriesInput.value = '';
            this.resultsHandler.reset();
            this.updateStartButton();
            UIManager.showNotification('All data cleared successfully', 'info');
        } catch (error) {
            console.error('Clear error:', error);
            UIManager.showNotification('Failed to clear data', 'error');
        }
    }

    async clearSelection() {
        if (this.resultsHandler.hasResults || this.resultsHandler.isProcessing()) {
            UIManager.showNotification('Cannot clear while processing or with results', 'info');
            return;
        }

        try {
            await fetch('/clear-uploads', { method: 'POST' });
            this.fileHandler.clear();
            this.updateStartButton();
            UIManager.showNotification('Selection cleared', 'info');
        } catch (error) {
            console.error('Clear error:', error);
            UIManager.showNotification('Failed to clear selection', 'error');
        }
    }

    async downloadResults() {
        try {
            const response = await fetch('/download');
            if (!response.ok) throw new Error('Download failed');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = "images.zip";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Download error:', error);
            UIManager.showNotification('Failed to download results', 'error');
        }
    }

    handleBeforeUnload(event) {
        if (this.resultsHandler.isProcessing() || this.resultsHandler.hasResults) {
            event.preventDefault();
            event.returnValue = '';
            return;
        }
        
        fetch('/cleanup', { 
            method: 'POST',
            keepalive: true 
        }).catch(console.error);
    }
}

// Initialize the application when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new App();
});