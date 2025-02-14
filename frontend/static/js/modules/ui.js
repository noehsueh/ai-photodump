export class UIManager {
    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    static updateStartButton(uploadedFiles, categoriesInput, startButton) {
        startButton.disabled = uploadedFiles.size === 0 || !categoriesInput.value.trim();
    }

    static setProcessingState(isProcessing) {
        if (isProcessing) {
            document.body.classList.add('is-processing');
        } else {
            document.body.classList.remove('is-processing');
        }
    }
}

// Initialize notification event listener
document.addEventListener('notification', (event) => {
    UIManager.showNotification(event.detail.message, event.detail.type);
});