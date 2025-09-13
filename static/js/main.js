
// Main JavaScript file for TDRMCD

// Initialize Socket.IO connection
let socket = null;
if (typeof io !== 'undefined') {
    if (!window.socket) {
        socket = io();
        window.socket = socket;
    } else {
        socket = window.socket;
    }
}

// Global variables
let currentUser = null;
let notifications = [];

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    // Notifications API is not implemented yet; disable to avoid 404s
    // initializeNotifications();
    initializeChat();
    initializeFileUpload();
    initializeMap();
});

// Initialize application
function initializeApp() {
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading states to buttons
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
                submitBtn.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });

    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
}

// Notification system
function initializeNotifications() {
    loadNotifications();
    
    // Mark notification as read
    document.addEventListener('click', function(e) {
        if (e.target.matches('.notification-item') || e.target.closest('.notification-item')) {
            const notificationItem = e.target.closest('.notification-item');
            const notificationId = notificationItem.dataset.notificationId;
            markNotificationRead(notificationId);
        }
    });

    // Mark all notifications as read
    const markAllReadBtn = document.getElementById('mark-all-read');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            markAllNotificationsRead();
        });
    }
}

function loadNotifications() {
    fetch('/api/notifications')
        .then(async response => {
            if (!response.ok) {
                // 404 or other errors: skip without throwing JSON parse error
                throw new Error(`HTTP ${response.status}`);
            }
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                throw new Error('Non-JSON response');
            }
            return response.json();
        })
        .then(data => {
            if (data && data.notifications) {
                updateNotificationUI(data.notifications);
            }
        })
        .catch(error => {
            // Quietly ignore in development if endpoint not implemented
            // console.warn('Notifications unavailable:', error.message);
        });
}

function updateNotificationUI(notifications) {
    const notificationsList = document.getElementById('notifications-list');
    const notificationCount = document.getElementById('notification-count');
    
    if (!notificationsList || !notificationCount) return;

    const unreadCount = notifications.filter(n => !n.is_read).length;
    notificationCount.textContent = unreadCount;
    notificationCount.style.display = unreadCount > 0 ? 'inline' : 'none';

    if (notifications.length === 0) {
        notificationsList.innerHTML = '<li><a class="dropdown-item text-muted" href="#">No notifications</a></li>';
        return;
    }

    notificationsList.innerHTML = notifications.map(notification => `
        <li>
            <a class="dropdown-item notification-item ${!notification.is_read ? 'fw-bold' : ''}" 
               href="#" data-notification-id="${notification.id}">
                <div class="d-flex">
                    <div class="flex-shrink-0 me-2">
                        <i class="fas fa-${getNotificationIcon(notification.type)} text-${getNotificationColor(notification.type)}"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div class="fw-bold">${notification.title}</div>
                        <div class="small text-muted">${notification.message}</div>
                        <div class="small text-muted">${formatDate(notification.created_at)}</div>
                    </div>
                </div>
            </a>
        </li>
    `).join('');
}

function markNotificationRead(notificationId) {
    fetch(`/api/notifications/mark_read/${notificationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadNotifications();
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

function markAllNotificationsRead() {
    fetch('/api/notifications/mark_all_read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadNotifications();
        }
    })
    .catch(error => console.error('Error marking all notifications as read:', error));
}

function getNotificationIcon(type) {
    const icons = {
        'info': 'info-circle',
        'success': 'check-circle',
        'warning': 'exclamation-triangle',
        'error': 'exclamation-circle'
    };
    return icons[type] || 'bell';
}

function getNotificationColor(type) {
    const colors = {
        'info': 'info',
        'success': 'success',
        'warning': 'warning',
        'error': 'danger'
    };
    return colors[type] || 'primary';
}

// Chat functionality
function initializeChat() {
    if (!socket) return;

    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer) return;

    const messagesContainer = document.querySelector('.chat-messages');
    const messageForm = document.querySelector('.message-form');
    const messageInput = document.querySelector('.message-input');

    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (message) {
                sendMessage(message);
                messageInput.value = '';
            }
        });
    }

    // Socket event listeners
    socket.on('receive_message', function(data) {
        displayMessage(data);
    });

    socket.on('user_joined', function(data) {
        displaySystemMessage(`${data.username} joined the chat`);
    });

    socket.on('user_left', function(data) {
        displaySystemMessage(`${data.username} left the chat`);
    });
}

function sendMessage(message) {
    if (!socket) return;
    
    const room = getCurrentChatRoom();
    socket.emit('send_message', {
        message: message,
        room: room
    });
}

function displayMessage(data) {
    const messagesContainer = document.querySelector('.chat-messages');
    if (!messagesContainer) return;

    const messageElement = document.createElement('div');
    messageElement.className = `message ${data.username === getCurrentUsername() ? 'own' : 'other'}`;
    messageElement.innerHTML = `
        <div class="message-content">${escapeHtml(data.message)}</div>
        <div class="message-time">${data.timestamp}</div>
    `;

    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function displaySystemMessage(message) {
    const messagesContainer = document.querySelector('.chat-messages');
    if (!messagesContainer) return;

    const messageElement = document.createElement('div');
    messageElement.className = 'message system text-center text-muted';
    messageElement.innerHTML = `<small><em>${escapeHtml(message)}</em></small>`;

    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function getCurrentChatRoom() {
    const roomElement = document.querySelector('[data-room]');
    return roomElement ? roomElement.dataset.room : 'general';
}

function getCurrentUsername() {
    const userElement = document.querySelector('[data-username]');
    return userElement ? userElement.dataset.username : '';
}

// File upload functionality
function initializeFileUpload() {
    const fileUploadAreas = document.querySelectorAll('.file-upload-area');
    
    fileUploadAreas.forEach(area => {
        const fileInput = area.querySelector('input[type="file"]');
        
        // Click to upload
        area.addEventListener('click', function() {
            fileInput.click();
        });

        // Drag and drop
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0], area);
            }
        });

        // File input change
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0], area);
            }
        });
    });
}

function handleFileSelect(file, uploadArea) {
    const fileName = uploadArea.querySelector('.file-name');
    const fileSize = uploadArea.querySelector('.file-size');
    
    if (fileName) {
        fileName.textContent = file.name;
    }
    
    if (fileSize) {
        fileSize.textContent = formatFileSize(file.size);
    }

    // Show file preview if it's an image
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            let preview = uploadArea.querySelector('.file-preview');
            if (!preview) {
                preview = document.createElement('div');
                preview.className = 'file-preview mt-2';
                uploadArea.appendChild(preview);
            }
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview" class="img-thumbnail" style="max-width: 200px;">`;
        };
        reader.readAsDataURL(file);
    }
}

// Map functionality
function initializeMap() {
    const mapContainer = document.getElementById('map');
    if (!mapContainer) return;

    // Initialize Leaflet map
    const map = L.map('map').setView([34.0151, 71.5249], 8); // KPK coordinates

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Load resource markers
    loadResourceMarkers(map);
}

function loadResourceMarkers(map) {
    const mapData = window.mapData || [];
    
    mapData.forEach(resource => {
        const marker = L.marker([resource.latitude, resource.longitude])
            .addTo(map)
            .bindPopup(`
                <div class="map-popup">
                    <h6>${resource.title}</h6>
                    <p class="small">${resource.description}</p>
                    <span class="badge bg-primary">${resource.category}</span>
                    ${resource.location ? `<br><small class="text-muted">${resource.location}</small>` : ''}
                </div>
            `);
    });
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return date.toLocaleDateString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

// Search functionality
function initializeSearch() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-input');
    
    if (searchInput) {
        // Add search suggestions
        searchInput.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            if (query.length > 2) {
                fetchSearchSuggestions(query);
            }
        }, 300));
    }
}

function fetchSearchSuggestions(query) {
    fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchSuggestions(data.suggestions);
        })
        .catch(error => console.error('Error fetching search suggestions:', error));
}

function displaySearchSuggestions(suggestions) {
    // Implementation for displaying search suggestions
    console.log('Search suggestions:', suggestions);
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global access
window.TDRMCD = {
    showToast,
    formatDate,
    formatFileSize,
    escapeHtml
};
