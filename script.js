// Dashboard State
let dashboardState = {
    aiActive: true,
    pendingApprovals: [],
    recentActivities: [],
    stats: {
        weeklyRevenue: 2450,
        pendingTasks: 8,
        unreadMessages: 5,
        aiUptime: 99.8
    }
};

// DOM Elements
const revenueChartEl = document.getElementById('revenueChart');
const taskChartEl = document.getElementById('taskChart');
const activityListEl = document.getElementById('activity-list');
const approvalListEl = document.getElementById('approval-list');
const approvalCountEl = document.getElementById('approval-count');
const modalEl = document.getElementById('approvalModal');
let currentApprovalId = null;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    loadDashboardData();
    setupEventListeners();
    startAutoRefresh();
});

// Initialize Charts
function initCharts() {
    // Revenue Chart
    new Chart(revenueChartEl, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Revenue ($)',
                data: [1500, 1800, 2200, 1950, 2450, 2800],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Task Completion Chart
    new Chart(taskChartEl, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'In Progress', 'Pending', 'Overdue'],
            datasets: [{
                data: [65, 15, 10, 10],
                backgroundColor: [
                    '#10b981',
                    '#2563eb',
                    '#f59e0b',
                    '#ef4444'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// Load Dashboard Data
async function loadDashboardData() {
    try {
        const response = await fetch('http://localhost:3000/api/dashboard');
        const data = await response.json();
        
        dashboardState = data;
        updateDashboardUI();
        updateStatsUI();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        loadSampleData();
    }
}

function loadSampleData() {
    dashboardState.recentActivities = [
        {
            id: 1,
            type: 'email',
            title: 'Invoice sent to Client A',
            description: 'Amount: $1,500',
            time: '10:45 AM',
            icon: 'fas fa-envelope',
            iconColor: '#2563eb'
        },
        {
            id: 2,
            type: 'whatsapp',
            title: 'WhatsApp message replied',
            description: 'Client inquiry about pricing',
            time: '9:30 AM',
            icon: 'fab fa-whatsapp',
            iconColor: '#25d366'
        },
        {
            id: 3,
            type: 'payment',
            title: 'Payment processed',
            description: 'Software subscription renewed',
            time: 'Yesterday',
            icon: 'fas fa-credit-card',
            iconColor: '#10b981'
        },
        {
            id: 4,
            type: 'social',
            title: 'LinkedIn post scheduled',
            description: 'Business update post',
            time: 'Yesterday',
            icon: 'fab fa-linkedin',
            iconColor: '#0077b5'
        }
    ];

    dashboardState.pendingApprovals = [
        {
            id: 1,
            type: 'email',
            title: 'Send invoice to Client B',
            description: 'Amount: $2,000 - Requires approval before sending',
            amount: 2000,
            recipient: 'client@example.com',
            action: 'send_email'
        },
        {
            id: 2,
            type: 'payment',
            title: 'Pay vendor invoice',
            description: 'Web hosting renewal - $89/month',
            amount: 89,
            recipient: 'Hosting Provider',
            action: 'make_payment'
        }
    ];

    updateDashboardUI();
}

// Update UI
function updateDashboardUI() {
    updateActivityList();
    updateApprovalList();
    updateStatsUI();
}

function updateActivityList() {
    activityListEl.innerHTML = '';
    dashboardState.recentActivities.forEach(activity => {
        const activityEl = document.createElement('div');
        activityEl.className = 'activity-item';
        activityEl.innerHTML = `
            <div class="activity-icon" style="background: ${activity.iconColor}">
                <i class="${activity.icon}"></i>
            </div>
            <div class="activity-info">
                <h4>${activity.title}</h4>
                <p>${activity.description}</p>
                <span class="activity-time">${activity.time}</span>
            </div>
        `;
        activityListEl.appendChild(activityEl);
    });
}

function updateApprovalList() {
    approvalListEl.innerHTML = '';
    approvalCountEl.textContent = dashboardState.pendingApprovals.length;
    
    dashboardState.pendingApprovals.forEach(approval => {
        const approvalEl = document.createElement('div');
        approvalEl.className = 'approval-item';
        approvalEl.innerHTML = `
            <div>
                <h4>${approval.title}</h4>
                <p>${approval.description}</p>
                <strong>Amount: $${approval.amount}</strong>
            </div>
            <div class="approval-actions">
                <button class="btn btn-sm btn-success" onclick="showApprovalModal(${approval.id})">
                    <i class="fas fa-check"></i> Review
                </button>
            </div>
        `;
        approvalListEl.appendChild(approvalEl);
    });
}

function updateStatsUI() {
    document.getElementById('weekly-revenue').textContent = `$${dashboardState.stats.weeklyRevenue}`;
    document.getElementById('pending-tasks').textContent = dashboardState.stats.pendingTasks;
    document.getElementById('unread-messages').textContent = dashboardState.stats.unreadMessages;
    document.getElementById('ai-uptime').textContent = `${dashboardState.stats.aiUptime}%`;
}

// Event Listeners
function setupEventListeners() {
    // Nav menu
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.nav-menu li').forEach(li => li.classList.remove('active'));
            this.parentElement.classList.add('active');
            // Add tab switching logic here
        });
    });
}

// Modal Functions
function showApprovalModal(approvalId) {
    const approval = dashboardState.pendingApprovals.find(a => a.id === approvalId);
    if (!approval) return;

    currentApprovalId = approvalId;
    const detailsEl = document.getElementById('approval-details');
    detailsEl.innerHTML = `
        <h4>${approval.title}</h4>
        <p>${approval.description}</p>
        <div class="approval-detail">
            <strong>Type:</strong> ${approval.type}
        </div>
        <div class="approval-detail">
            <strong>Amount:</strong> $${approval.amount}
        </div>
        <div class="approval-detail">
            <strong>Recipient:</strong> ${approval.recipient}
        </div>
        <div class="approval-detail">
            <strong>Action:</strong> ${approval.action}
        </div>
    `;
    modalEl.style.display = 'flex';
}

function closeModal() {
    modalEl.style.display = 'none';
    currentApprovalId = null;
}

async function approveAction() {
    if (!currentApprovalId) return;
    
    try {
        const response = await fetch('http://localhost:3000/api/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approvalId: currentApprovalId, action: 'approve' })
        });
        
        if (response.ok) {
            dashboardState.pendingApprovals = dashboardState.pendingApprovals.filter(
                a => a.id !== currentApprovalId
            );
            updateDashboardUI();
            showNotification('Action approved successfully!', 'success');
        }
    } catch (error) {
        console.error('Error approving action:', error);
        showNotification('Error approving action', 'error');
    }
    
    closeModal();
}

async function rejectAction() {
    if (!currentApprovalId) return;
    
    try {
        const response = await fetch('http://localhost:3000/api/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approvalId: currentApprovalId, action: 'reject' })
        });
        
        if (response.ok) {
            dashboardState.pendingApprovals = dashboardState.pendingApprovals.filter(
                a => a.id !== currentApprovalId
            );
            updateDashboardUI();
            showNotification('Action rejected.', 'info');
        }
    } catch (error) {
        console.error('Error rejecting action:', error);
        showNotification('Error rejecting action', 'error');
    }
    
    closeModal();
}

// Dashboard Actions
function toggleAI() {
    dashboardState.aiActive = !dashboardState.aiActive;
    const statusIndicator = document.querySelector('.status-indicator .status');
    const toggleBtn = document.querySelector('.header-actions .btn-secondary');
    
    if (dashboardState.aiActive) {
        statusIndicator.classList.add('active');
        toggleBtn.innerHTML = '<i class="fas fa-power-off"></i> Pause AI';
        showNotification('AI Employee activated', 'success');
    } else {
        statusIndicator.classList.remove('active');
        toggleBtn.innerHTML = '<i class="fas fa-power-off"></i> Activate AI';
        showNotification('AI Employee paused', 'warning');
    }
}

function runAudit() {
    showNotification('Running business audit...', 'info');
    setTimeout(() => {
        showNotification('Audit completed successfully!', 'success');
    }, 2000);
}

function processEmails() {
    showNotification('Processing emails...', 'info');
    // Implement email processing logic
}

function generateReport() {
    showNotification('Generating CEO briefing...', 'info');
    // Implement report generation logic
}

function checkWhatsApp() {
    showNotification('Checking WhatsApp messages...', 'info');
    // Implement WhatsApp checking logic
}

function auditFinances() {
    showNotification('Auditing finances...', 'info');
    // Implement finance audit logic
}

function refreshActivity() {
    loadDashboardData();
    showNotification('Refreshing data...', 'info');
}

// Helper Functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#f59e0b'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function startAutoRefresh() {
    setInterval(() => {
        if (dashboardState.aiActive) {
            loadDashboardData();
        }
    }, 30000); // Refresh every 30 seconds
}

// Add notification styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);