export class ResultsHandler {
    constructor(resultsSection, resultsGrid, processingSection, statusText) {
        this.resultsSection = resultsSection;
        this.resultsGrid = resultsGrid;
        this.processingSection = processingSection;
        this.statusText = statusText;
        this.hasResults = false;
        this.processing = false;
    }

    displayResults(results) {
        this.resultsSection.classList.remove('hidden');
        this.resultsGrid.innerHTML = '';
        this.processingSection.classList.add('hidden');

        window.processedCategories = results;
        this.hasResults = true;

        Object.entries(results).forEach(([category, photos]) => {
            if (!photos.length) return;
            
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'category';
            categoryDiv.innerHTML = `<h3>${category}</h3>`;

            const photosGrid = document.createElement('div');
            photosGrid.className = 'photos-grid';

            photos.forEach(photoPath => {
                const imgContainer = document.createElement('div');
                imgContainer.className = 'img-container';
                
                const img = document.createElement('img');
                const filename = photoPath.split('/').pop();
                img.src = `/uploads/${filename}`;
                img.alt = `${category} - ${filename}`;
                img.loading = 'lazy';
                img.onclick = () => {
                    const event = new CustomEvent('openModal', { 
                        detail: { src: img.src }
                    });
                    document.dispatchEvent(event);
                };
                
                imgContainer.appendChild(img);
                photosGrid.appendChild(imgContainer);
            });

            categoryDiv.appendChild(photosGrid);
            this.resultsGrid.appendChild(categoryDiv);
        });
        
        document.getElementById('download-button').disabled = false;
    }

    async startProcessing(categories) {
        if (this.processing) {
            const event = new CustomEvent('notification', {
                detail: { message: 'Processing already in progress', type: 'error' }
            });
            document.dispatchEvent(event);
            return;
        }

        this.processing = true;
        this.processingSection.classList.remove('hidden');
        
        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(categories)
            });

            if (!response.ok) throw new Error('Processing failed');
            const results = await response.json();
            this.displayResults(results);
        } catch (error) {
            console.error('Processing error:', error);
            const event = new CustomEvent('notification', {
                detail: { message: 'Processing failed', type: 'error' }
            });
            document.dispatchEvent(event);
            this.processingSection.classList.add('hidden');
        } finally {
            this.processing = false;
        }
    }

    updateStatus(data) {
        switch (data.status) {
            case 'categorizing':
                this.processingSection.classList.remove('hidden');
                this.statusText.textContent = 'Analyzing and categorizing photos...';
                break;
                
            case 'processing':
                this.statusText.textContent = 'Processing and ranking photos...';
                break;
                
            case 'complete':
                this.processingSection.classList.add('hidden');
                this.displayResults(data.results);
                const event = new CustomEvent('notification', {
                    detail: { message: 'Processing complete!', type: 'info' }
                });
                document.dispatchEvent(event);
                break;
                
            case 'cleared':
                this.reset();
                break;
                
            case 'cancelled':
                this.processingSection.classList.add('hidden');
                const cancelEvent = new CustomEvent('notification', {
                    detail: { message: 'Processing cancelled', type: 'info' }
                });
                document.dispatchEvent(cancelEvent);
                break;
                
            case 'error':
                this.processingSection.classList.add('hidden');
                const errorEvent = new CustomEvent('notification', {
                    detail: { message: data.message || 'An error occurred', type: 'error' }
                });
                document.dispatchEvent(errorEvent);
                break;
        }
    }

    reset() {
        this.hasResults = false;
        this.processing = false;
        this.resultsSection.classList.add('hidden');
        this.processingSection.classList.add('hidden');
    }

    isProcessing() {
        return this.processing;
    }
}