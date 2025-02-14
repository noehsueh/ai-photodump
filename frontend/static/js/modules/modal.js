export class ModalManager {
    constructor() {
        this.modal = document.getElementById('image-modal');
        this.modalImage = document.getElementById('modal-image');
        this.modalImages = [];
        this.currentModalImageIndex = 0;

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close button
        document.querySelector('.close').onclick = () => this.closeModal();

        // Click outside to close
        this.modal.onclick = (e) => {
            if (e.target === this.modal) this.closeModal();
        };

        // Navigation buttons
        document.querySelectorAll('.modal-nav').forEach(nav => {
            nav.onclick = (e) => {
                e.stopPropagation();
                this.navigateModal(nav.classList.contains('prev') ? -1 : 1);
            };
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!this.modal.classList.contains('show')) return;
            
            switch(e.key) {
                case 'Escape': 
                    e.preventDefault();
                    this.closeModal(); 
                    break;
                case 'ArrowLeft': 
                    e.preventDefault();
                    this.navigateModal(-1); 
                    break;
                case 'ArrowRight': 
                    e.preventDefault();
                    this.navigateModal(1); 
                    break;
            }
        });

        // Image load handler
        this.modalImage.addEventListener('load', () => {
            this.modalImage.classList.add('loaded');
        });

        // Navigation zones
        document.querySelectorAll('.nav-hover-zone').forEach(zone => {
            zone.onclick = (e) => {
                e.stopPropagation();
                this.navigateModal(zone.classList.contains('left') ? -1 : 1);
            };
        });

        // Custom open modal event
        document.addEventListener('openModal', (event) => {
            this.openModal(event.detail.src);
        });
    }

    openModal(imageSrc) {
        this.modalImage.src = '';
        this.modalImage.classList.remove('loaded');
        this.modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        const container = document.getElementById('results-section').classList.contains('hidden') 
            ? document.getElementById('preview-grid')
            : document.getElementById('results-grid');
        
        this.modalImages = Array.from(container.querySelectorAll('img')).map(img => img.src);
        this.currentModalImageIndex = this.modalImages.indexOf(imageSrc);
        
        const img = new Image();
        img.onload = () => {
            this.modalImage.src = imageSrc;
            this.modalImage.classList.add('loaded');
        };
        img.src = imageSrc;
        
        this.updateModalNavigation();
        
        const shortcuts = document.querySelector('.modal-shortcuts');
        shortcuts.classList.add('initial');
        setTimeout(() => shortcuts.classList.remove('initial'), 3000);
    }

    closeModal() {
        this.modal.classList.remove('show');
        document.body.style.overflow = '';
    }

    navigateModal(direction) {
        if (this.modalImages.length <= 1) return;
        
        this.currentModalImageIndex = (this.currentModalImageIndex + direction + this.modalImages.length) % this.modalImages.length;
        this.modalImage.src = this.modalImages[this.currentModalImageIndex];
    }

    updateModalNavigation() {
        const prevNav = document.querySelector('.modal-nav.prev');
        const nextNav = document.querySelector('.modal-nav.next');
        
        if (this.modalImages.length <= 1) {
            prevNav.style.display = 'none';
            nextNav.style.display = 'none';
        } else {
            prevNav.style.display = '';
            nextNav.style.display = '';
        }
    }
}