export class FileHandler {
    constructor(previewGrid) {
        this.uploadedFiles = new Map();
        this.previewGrid = previewGrid;
    }

    async handleFiles(files) {
        const formData = new FormData();
        let newFiles = false;
        let duplicates = 0;

        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                if (!this.uploadedFiles.has(file.name)) {
                    formData.append('files', file);
                    this.uploadedFiles.set(file.name, null);
                    newFiles = true;
                } else {
                    duplicates++;
                }
            }
        });

        if (newFiles) {
            await this.uploadFiles(formData);
        }

        if (duplicates > 0) {
            const event = new CustomEvent('notification', {
                detail: { message: `${duplicates} file(s) skipped (already selected)`, type: 'info' }
            });
            document.dispatchEvent(event);
        }

        return this.uploadedFiles.size;
    }

    async uploadFiles(formData) {
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            data.files.forEach(filename => {
                if (!document.querySelector(`[data-filename="${filename}"]`)) {
                    this.displayPreviewFromPath(`/uploads/${filename}`);
                }
            });

            if (data.skipped > 0) {
                const event = new CustomEvent('notification', {
                    detail: { message: `${data.skipped} files skipped (already exist)`, type: 'info' }
                });
                document.dispatchEvent(event);
            }
        } catch (error) {
            console.error('Upload error:', error);
            const event = new CustomEvent('notification', {
                detail: { message: 'Failed to upload files', type: 'error' }
            });
            document.dispatchEvent(event);
        }
    }

    displayPreviewFromPath(path) {
        const filename = path.split('/').pop();
        const imgContainer = document.createElement('div');
        imgContainer.className = 'img-container preview';
        imgContainer.dataset.filename = filename;
        
        const removeButton = document.createElement('div');
        removeButton.className = 'remove-photo';
        removeButton.innerHTML = '×';
        removeButton.onclick = async (e) => {
            e.stopPropagation();
            await this.removeFile(filename);
        };
        
        const img = document.createElement('img');
        img.src = path;
        img.alt = filename;
        img.loading = 'lazy';
        img.onclick = () => {
            const event = new CustomEvent('openModal', { detail: { src: path } });
            document.dispatchEvent(event);
        };
        
        imgContainer.appendChild(removeButton);
        imgContainer.appendChild(img);
        this.previewGrid.appendChild(imgContainer);
    }

    async removeFile(filename) {
        try {
            const response = await fetch(`/remove-file`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            });
            
            if (!response.ok) throw new Error('Failed to remove file');
            
            this.uploadedFiles.delete(filename);
            const imgContainer = document.querySelector(`[data-filename="${filename}"]`);
            if (imgContainer) {
                imgContainer.remove();
            }
            return this.uploadedFiles.size;
        } catch (error) {
            console.error('Remove error:', error);
            const event = new CustomEvent('notification', {
                detail: { message: 'Failed to remove file', type: 'error' }
            });
            document.dispatchEvent(event);
        }
    }

    async loadExistingPhotos() {
        try {
            const response = await fetch('/list-uploads');
            if (!response.ok) {
                this.uploadedFiles.clear();
                this.previewGrid.innerHTML = '';
                return 0;
            }
            
            const files = await response.json();
            this.uploadedFiles.clear();
            this.previewGrid.innerHTML = '';
            
            files.forEach(filename => {
                this.uploadedFiles.set(filename, null);
                this.displayPreviewFromPath(`/uploads/${filename}`);
            });
            
            return this.uploadedFiles.size;
        } catch (error) {
            console.error('Load error:', error);
            this.uploadedFiles.clear();
            this.previewGrid.innerHTML = '';
            return 0;
        }
    }

    clear() {
        this.uploadedFiles.clear();
        this.previewGrid.innerHTML = '';
    }

    get size() {
        return this.uploadedFiles.size;
    }
}