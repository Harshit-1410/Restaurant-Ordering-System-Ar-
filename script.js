document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.querySelector('.search-input');
    const searchBtn = document.querySelector('.search-btn');
    
    searchBtn.addEventListener('click', function() {
        const searchTerm = searchInput.value.trim();
        if (searchTerm) {
            console.log('Searching for:', searchTerm);
            // Here you would implement actual search functionality
            alert(`Searching for: ${searchTerm}`);
        }
    });
    
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchBtn.click();
        }
    });

    // AR functionality with model-viewer support
    function isARSupported() {
        // Check for iOS Safari (USDZ support)
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
        
        // Check for WebXR support (Android/Chrome)
        const hasWebXR = 'xr' in navigator;
        
        return (isIOS && isSafari) || hasWebXR || 'model-viewer' in window;
    }

    function createModelViewer(usdzPath, glbPath, itemName) {
        const modelViewer = document.createElement('model-viewer');
        modelViewer.setAttribute('src', glbPath);
        modelViewer.setAttribute('ios-src', usdzPath);
        modelViewer.setAttribute('alt', `3D model of ${itemName}`);
        modelViewer.setAttribute('ar', '');
        modelViewer.setAttribute('ar-modes', 'webxr scene-viewer quick-look');
        modelViewer.setAttribute('camera-controls', '');
        modelViewer.setAttribute('auto-rotate', '');
        modelViewer.setAttribute('style', 'width: 100%; height: 300px; background-color: #f0f0f0;');
        
        return modelViewer;
    }

    // AR button functionality
    const arButtons = document.querySelectorAll('.ar-btn');
    arButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const menuItem = this.closest('.menu-item');
            const itemName = menuItem.querySelector('h3').textContent;
            const usdzPath = menuItem.dataset.usdz;
            const glbPath = menuItem.dataset.glb;
            const previewContainer = menuItem.querySelector('.inline-ar-preview');
            
            // Add visual feedback
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            if (!usdzPath && !glbPath) {
                // No AR files available
                console.log(`AR view requested for: ${itemName}`);
                alert(`🥽 AR view for ${itemName}!\n\nThis item doesn't have an AR model available yet.`);
                return;
            }
            
            // Check device capabilities
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
            const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
            
            if (isIOS && isSafari && usdzPath) {
                // iOS Safari - use direct USDZ link for AR Quick Look
                const arLink = document.createElement('a');
                arLink.href = usdzPath;
                arLink.rel = 'ar';
                arLink.style.display = 'none';
                document.body.appendChild(arLink);
                arLink.click();
                document.body.removeChild(arLink);
                
                console.log(`Launching AR Quick Look for: ${itemName}`);
                showNotification(`🥽 Opening AR view for ${itemName}...`);
            } else if (glbPath) {
                // Other devices - use model-viewer for inline preview and WebXR
                if (previewContainer.style.display === 'none') {
                    // Show inline 3D preview
                    previewContainer.innerHTML = '';
                    const modelViewer = createModelViewer(usdzPath, glbPath, itemName);
                    previewContainer.appendChild(modelViewer);
                    previewContainer.style.display = 'block';
                    
                    // Add AR button to model viewer if supported
                    if (isARSupported()) {
                        const arButton = document.createElement('button');
                        arButton.textContent = '📱 View in AR';
                        arButton.style.cssText = `
                            position: absolute;
                            top: 10px;
                            right: 10px;
                            background: rgba(0,0,0,0.7);
                            color: white;
                            border: none;
                            padding: 8px 12px;
                            border-radius: 20px;
                            font-size: 12px;
                            cursor: pointer;
                        `;
                        
                        arButton.addEventListener('click', () => {
                            modelViewer.activateAR();
                        });
                        
                        modelViewer.style.position = 'relative';
                        modelViewer.appendChild(arButton);
                    }
                    
                    console.log(`Showing 3D preview for: ${itemName}`);
                    showNotification(`🎯 3D preview loaded for ${itemName}`);
                } else {
                    // Hide inline preview
                    previewContainer.style.display = 'none';
                    previewContainer.innerHTML = '';
                }
            } else {
                // Fallback message
                alert(`📱 AR Preview\n\nAR viewing requires:\n• iOS Safari for USDZ files\n• Android Chrome for WebXR\n\nThis ${itemName} model may not be compatible with your device.`);
            }
        });
    });





    // Menu button functionality
    const menuBtn = document.querySelector('.menu-btn');
    menuBtn.addEventListener('click', function() {
        console.log('Menu button clicked');
        alert('Menu opened! This would show navigation options.');
    });





    // See more link
    const seeMoreLink = document.querySelector('.see-more-link');
    if (seeMoreLink) {
        seeMoreLink.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('See more clicked');
            alert('Loading more menu items...');
        });
    }

    // Utility function to show notifications
    function showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: 500;
            z-index: 1000;
            animation: slideDown 0.3s ease;
        `;
        
        // Add animation keyframes
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideDown {
                    from {
                        opacity: 0;
                        transform: translateX(-50%) translateY(-20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(-50%) translateY(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideDown 0.3s ease reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Add smooth scrolling for better UX
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add loading states for better UX
    function addLoadingState(button, duration = 1000) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, duration);
    }

    console.log('Menu website loaded successfully!');
});
