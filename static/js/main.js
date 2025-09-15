
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
    initializeNotifications();
    initializeChat();
    initializeFileUpload();
    initializeMap();
    initializeNavbarSearch();
    initializeRevealOnScroll();
    initializeCounters();
    initializeHeroBubbles();
});

// Initialize application
function initializeApp() {
    // Add smooth scrolling for anchor links only (not external URLs)
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Only handle if it's a valid CSS selector (starts with # and has valid characters)
            if (href && href.startsWith('#') && href.length > 1 && /^#[a-zA-Z0-9_-]+$/.test(href)) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Add loading states to buttons (skip navbar search with .no-loading)
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            if (form.classList.contains('no-loading')) return;
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
    // Poll every 30s for new notifications
    setInterval(loadNotifications, 30000);
    
    // Mark notification as read
    document.addEventListener('click', function(e) {
        if (e.target.matches('.notification-item') || e.target.closest('.notification-item')) {
            const notificationItem = e.target.closest('.notification-item');
            const notificationId = notificationItem.dataset.notificationId;
            // Optimistically decrement without flicker
            const badge = document.getElementById('notification-count');
            if (badge && badge.textContent) {
                const curr = parseInt(badge.textContent, 10) || 0;
                if (curr > 0) {
                    const next = curr - 1;
                    if (badge.textContent !== String(next)) badge.textContent = String(next);
                    if (next === 0) badge.style.display = 'none';
                }
            }
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
    if (unreadCount > 0) {
        if (notificationCount.textContent !== String(unreadCount)) {
            notificationCount.textContent = unreadCount;
        }
        notificationCount.style.display = 'inline';
    } else {
        notificationCount.style.display = 'none';
        notificationCount.textContent = '';
    }

    if (notifications.length === 0) {
        notificationsList.innerHTML = '<a class="dropdown-item text-muted" href="#">No notifications</a>';
        return;
    }

    notificationsList.innerHTML = notifications.map(notification => `
        <a class="dropdown-item notification-item ${!notification.is_read ? 'fw-bold unread-notification' : ''}" 
           href="${notification.url || resolveNotificationUrl(notification)}" data-notification-id="${notification.id}">
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

function resolveNotificationUrl(notification) {
    // Heuristic linking based on message/title keywords
    const m = (notification.message || '').toLowerCase() + ' ' + (notification.title || '').toLowerCase();
    // Post related
    if (m.includes('post')) {
        // Expect message may include an id pattern like [#123], otherwise fall back to community index
        const idMatch = m.match(/#(\d+)/);
        if (idMatch) {
            return `/community/post/${idMatch[1]}`;
        }
        return '/community/';
    }
    // Comment related - try to navigate to post detail comments anchor
    if (m.includes('comment')) {
        const idMatch = m.match(/post\s*#(\d+)/);
        if (idMatch) {
            return `/community/post/${idMatch[1]}#comments`;
        }
        return '/community/';
    }
    return '/';
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
    escapeHtml,
    validateSearch
};

// Navbar search enhancements
function initializeNavbarSearch() {
    const input = document.getElementById('navbar-search');
    if (!input) return;
    const phrases = [
        'Search resources, posts, users',
        'Search posts, users, resources',
        'Search users, resources, posts'
    ];
    let pIndex = 0;
    let charIndex = 0;
    let typing = true;
    let intervalId = null;

    function typeStep() {
        const text = phrases[pIndex];
        if (typing) {
            charIndex++;
            input.setAttribute('placeholder', text.slice(0, charIndex) + '...');
            if (charIndex >= text.length) {
                typing = false;
                setTimeout(() => {}, 1000);
            }
        } else {
            charIndex--;
            input.setAttribute('placeholder', text.slice(0, Math.max(0, charIndex)) + '...');
            if (charIndex <= 0) {
                typing = true;
                pIndex = (pIndex + 1) % phrases.length;
            }
        }
    }

    function startTypewriter() {
        if (intervalId) clearInterval(intervalId);
        intervalId = setInterval(typeStep, 80);
    }
    function stopTypewriter() {
        if (intervalId) clearInterval(intervalId);
    }

    // Pause on focus for user convenience
    input.addEventListener('focus', stopTypewriter);
    input.addEventListener('blur', startTypewriter);
    startTypewriter();
}

function validateSearch(e) {
    const input = document.getElementById('navbar-search');
    if (!input) return true;
    const q = (input.value || '').trim();
    if (!q) {
        e && e.preventDefault();
        TDRMCD.showToast('Please enter something to search.', 'warning');
        return false;
    }
    return true;
}

// Reveal on scroll
function initializeRevealOnScroll() {
    const containers = document.querySelectorAll('.reveal-on-scroll');
    if (!containers.length) return;
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const targets = entry.target.querySelectorAll('.card, .activity-item');
                targets.forEach((el, i) => {
                    setTimeout(() => el.classList.add('is-visible'), i * 80);
                });
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2
    });
    containers.forEach(c => observer.observe(c));
}

function initializeCounters() {
    const counters = document.querySelectorAll('[data-counter]');
    if (!counters.length) return;
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.8 });
    counters.forEach(el => observer.observe(el));
}

function animateCounter(el) {
    const target = parseInt(el.getAttribute('data-target') || '0', 10);
    const duration = 1200;
    const start = performance.now();
    function step(now) {
        const progress = Math.min(1, (now - start) / duration);
        const value = Math.floor(progress * target);
        el.textContent = value.toLocaleString();
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

// Hero bubbles / hearts with messages
function initializeHeroBubbles() {
    const container = document.querySelector('.hero-bubbles');
    if (!container) return;
    const messages = [
        'Peace', 'Growth', 'Love', 'Unity', 'Hope', 'Sustainability',
        'Prosperity', 'Respect', 'Community', 'Harmony', 'Resilience'
    ];
    const icons = ['❤', '★', '✦', '✳', '◆'];

    function spawnBubble() {
        const el = document.createElement('div');
        el.className = 'bubble';
        const useIcon = Math.random() < 0.4;
        const text = useIcon ? icons[Math.floor(Math.random()*icons.length)] : messages[Math.floor(Math.random()*messages.length)];
        el.textContent = text;
        const left = Math.floor(Math.random() * 90) + 5; // 5% - 95%
        el.style.left = left + '%';
        el.style.fontSize = (useIcon ? (12 + Math.random()*10) : (12 + Math.random()*6)) + 'px';
        el.style.setProperty('--drift', (Math.random() * 80 - 40) + 'px');
        container.appendChild(el);
        // Remove after animation
        setTimeout(() => { if (el.parentNode) el.parentNode.removeChild(el); }, 6000);
    }

    // Spawn a few initially, then at intervals
    for (let i = 0; i < 4; i++) setTimeout(spawnBubble, i * 400);
    setInterval(spawnBubble, 1200);
}
