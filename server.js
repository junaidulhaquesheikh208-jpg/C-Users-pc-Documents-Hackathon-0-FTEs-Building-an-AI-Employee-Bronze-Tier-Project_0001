const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs').promises;
const { WebSocketServer } = require('ws');
const cron = require('node-cron');
const winston = require('winston');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../client')));

// Logger setup
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

// Obsidian vault path
const VAULT_PATH = path.join(__dirname, '../obsidian_vault');

// Ensure vault structure exists
async function initVault() {
    const folders = [
        'Needs_Action',
        'Plans',
        'Done',
        'Logs',
        'Pending_Approval',
        'Approved',
        'In_Progress',
        'Updates'
    ];

    for (const folder of folders) {
        const folderPath = path.join(VAULT_PATH, folder);
        try {
            await fs.mkdir(folderPath, { recursive: true });
        } catch (error) {
            logger.error(`Error creating folder ${folder}:`, error);
        }
    }

    // Create initial files if they don't exist
    const initialFiles = [
        { name: 'Dashboard.md', template: getDashboardTemplate() },
        { name: 'Company_Handbook.md', template: getCompanyHandbookTemplate() },
        { name: 'Business_Goals.md', template: getBusinessGoalsTemplate() }
    ];

    for (const file of initialFiles) {
        const filePath = path.join(VAULT_PATH, file.name);
        try {
            await fs.access(filePath);
        } catch {
            await fs.writeFile(filePath, file.template);
            logger.info(`Created ${file.name}`);
        }
    }
}

// File templates
function getDashboardTemplate() {
    return `---
last_updated: ${new Date().toISOString()}
status: active
---


# AI Employee Dashboard


## Current Status
- **AI Status**: Active
- **Last Audit**: Today
- **Uptime**: 99.8%


## Pending Actions
- [ ] Review emails (5 unread)
- [ ] Process WhatsApp messages (2 urgent)
- [ ] Generate weekly report


## Recent Activity
- ${new Date().toLocaleDateString()}: System initialized
- ${new Date().toLocaleDateString()}: Dashboard created


## Quick Stats
- Weekly Revenue: $2,450
- Tasks Completed: 42
- Messages Processed: 128
`;
}

function getCompanyHandbookTemplate() {
    return `---
version: 1.0
effective_date: ${new Date().toISOString().split('T')[0]}
---


# Company Handbook


## Communication Rules


### Email Etiquette
- Always be polite and professional
- Respond within 24 hours for business emails
- Flag urgent messages with "[URGENT]" prefix
- Never share sensitive information via email


### WhatsApp/SMS Rules
- Business hours: 9 AM - 6 PM (monitoring only)
- Emergency keywords: "urgent", "asap", "emergency", "help"
- Personal messages: do not respond automatically
- Payment discussions: always verify via email


## Financial Rules


### Approval Thresholds
- Payments under $50: auto-approve (recurring only)
- Payments $50-$100: flag for review
- Payments over $100: require explicit approval
- New payees: always require approval


### Subscription Management
- Flag unused subscriptions after 30 days of inactivity
- Alert on price increases > 20%
- Review all subscriptions monthly


## Social Media Rules


### Posting Guidelines
- Professional tone for LinkedIn
- Friendly tone for Instagram/Facebook
- Never post political/controversial content
- All posts require approval before publishing


### Response Rules
- Positive comments: thank the user
- Negative comments: escalate to human
- Questions: provide helpful information
- Spam: ignore and delete


## Security Rules


### Data Protection
- Never store passwords in plain text
- Use environment variables for API keys
- Encrypt sensitive files
- Regular backup of vault data


### Access Control
- Never share login credentials
- Use 2FA where available
- Rotate API keys monthly
- Log all access attempts


## Error Handling


### When in Doubt
1. Pause and alert human
2. Document the uncertainty
3. Wait for instructions
4. Never assume


### Recovery Procedures
- API failures: retry 3 times with exponential backoff
- File errors: quarantine and alert
- System crashes: auto-restart with watchdog
`;
}

function getBusinessGoalsTemplate() {
    return `---
quarter: Q1 2026
last_updated: ${new Date().toISOString().split('T')[0]}
---


# Business Goals - Q1 2026


## Revenue Targets
- **Monthly Goal**: $10,000
- **Quarter Goal**: $30,000
- **Current MTD**: $4,500


## Key Performance Indicators


### Response Times
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Email response | < 24 hours | > 48 hours |
| WhatsApp response | < 2 hours | > 6 hours |
| Invoice processing | < 1 hour | > 4 hours |


### Financial Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |
| Profit margin | > 30% | < 20% |


## Active Projects


### Project Alpha
- **Deadline**: Jan 15, 2026
- **Budget**: $2,000
- **Status**: In progress
- **Milestones**:
  - [x] Initial planning
  - [ ] Design phase
  - [ ] Development
  - [ ] Testing
  - [ ] Delivery


### Project Beta
- **Deadline**: Jan 30, 2026
- **Budget**: $3,500
- **Status**: Planning
- **Milestones**:
  - [x] Requirements gathering
  - [ ] Proposal submission
  - [ ] Contract signing
  - [ ] Project kickoff


## Subscription Audit Rules


### Review Criteria
Flag for review if:
- No login/usage in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool
- Can be replaced with free alternative


### Essential Services
- Google Workspace ($12/month)
- Notion Team ($8/user/month)
- GitHub Pro ($4/month)
- Domain hosting ($15/month)


## Growth Initiatives


### Client Acquisition
- Target 5 new clients this quarter
- Focus on referral program
- LinkedIn outreach campaign


### Service Expansion
- Research new service offerings
- Create service packages
- Update pricing strategy
`;
}

// API Routes

// Get dashboard data
app.get('/api/dashboard', async (req, res) => {
    try {
        const dashboardData = await getDashboardData();
        res.json(dashboardData);
    } catch (error) {
        logger.error('Error fetching dashboard:', error);
        res.status(500).json({ error: 'Failed to load dashboard' });
    }
});

// Get pending approvals
app.get('/api/approvals', async (req, res) => {
    try {
        const approvals = await getPendingApprovals();
        res.json(approvals);
    } catch (error) {
        logger.error('Error fetching approvals:', error);
        res.status(500).json({ error: 'Failed to load approvals' });
    }
});

// Approve/reject action
app.post('/api/approve', async (req, res) => {
    try {
        const { approvalId, action } = req.body;
        
        if (!approvalId || !action) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        // Update approval status
        await updateApprovalStatus(approvalId, action);
        
        // If approved, execute the action
        if (action === 'approve') {
            await executeApprovedAction(approvalId);
        }

        // Log the action
        await logAction({
            type: 'approval',
            action: action,
            approvalId: approvalId,
            timestamp: new Date().toISOString()
        });

        res.json({ success: true, message: `Action ${action}d successfully` });
    } catch (error) {
        logger.error('Error processing approval:', error);
        res.status(500).json({ error: 'Failed to process approval' });
    }
});

// Trigger AI processing
app.post('/api/process', async (req, res) => {
    try {
        const { action, data } = req.body;
        
        switch (action) {
            case 'emails':
                await processEmails();
                break;
            case 'whatsapp':
                await processWhatsApp();
                break;
            case 'audit':
                await runBusinessAudit();
                break;
            case 'report':
                await generateReport();
                break;
            default:
                throw new Error('Unknown action');
        }

        res.json({ success: true, message: `${action} processing started` });
    } catch (error) {
        logger.error('Error processing action:', error);
        res.status(500).json({ error: error.message });
    }
});

// Health check
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
            orchestrator: 'running',
            watchers: 'active',
            mcp_servers: 'connected'
        }
    });
});

// Helper functions
async function getDashboardData() {
    const dashboardPath = path.join(VAULT_PATH, 'Dashboard.md');
    const statsPath = path.join(VAULT_PATH, 'Logs/stats.json');
    
    try {
        const [dashboardContent, statsContent] = await Promise.all([
            fs.readFile(dashboardPath, 'utf-8'),
            fs.readFile(statsPath, 'utf-8').catch(() => '{}')
        ]);

        const stats = JSON.parse(statsContent);
        const approvals = await getPendingApprovals();
        const activities = await getRecentActivities();

        return {
            aiActive: true,
            pendingApprovals: approvals,
            recentActivities: activities,
            stats: {
                weeklyRevenue: stats.weeklyRevenue || 2450,
                pendingTasks: stats.pendingTasks || 8,
                unreadMessages: stats.unreadMessages || 5,
                aiUptime: stats.aiUptime || 99.8
            },
            dashboardContent
        };
    } catch (error) {
        logger.error('Error getting dashboard data:', error);
        return getDefaultDashboardData();
    }
}

async function getPendingApprovals() {
    const pendingDir = path.join(VAULT_PATH, 'Pending_Approval');
    try {
        const files = await fs.readdir(pendingDir);
        const approvals = [];
        
        for (const file of files) {
            if (file.endsWith('.md')) {
                const content = await fs.readFile(path.join(pendingDir, file), 'utf-8');
                const metadata = parseFrontmatter(content);
                
                approvals.push({
                    id: parseInt(file.split('_')[1]) || Date.now(),
                    file: file,
                    ...metadata,
                    title: metadata.subject || metadata.action,
                    description: metadata.description || 'Requires approval',
                    amount: metadata.amount || 0,
                    recipient: metadata.recipient || 'Unknown'
                });
            }
        }
        
        return approvals;
    } catch (error) {
        logger.error('Error reading pending approvals:', error);
        return [];
    }
}

async function getRecentActivities() {
    const logsDir = path.join(VAULT_PATH, 'Logs');
    try {
        const today = new Date().toISOString().split('T')[0];
        const logFile = path.join(logsDir, `${today}.json`);
        
        let activities = [];
        try {
            const logContent = await fs.readFile(logFile, 'utf-8');
            const logs = JSON.parse(logContent);
            activities = logs.slice(-10).map(log => ({
                id: log.timestamp,
                type: log.action_type,
                title: getActivityTitle(log),
                description: getActivityDescription(log),
                time: new Date(log.timestamp).toLocaleTimeString(),
                icon: getActivityIcon(log.action_type),
                iconColor: getActivityColor(log.action_type)
            }));
        } catch {
            // If no log file exists, return sample activities
            activities = getSampleActivities();
        }
        
        return activities;
    } catch (error) {
        logger.error('Error reading recent activities:', error);
        return getSampleActivities();
    }
}

function getActivityTitle(log) {
    const actions = {
        'email_send': 'Email sent',
        'whatsapp_reply': 'WhatsApp replied',
        'payment_processed': 'Payment processed',
        'social_post': 'Social media post',
        'audit_completed': 'Audit completed'
    };
    return actions[log.action_type] || 'Action performed';
}

function getActivityDescription(log) {
    return log.description || `Action: ${log.action_type}`;
}

function getActivityIcon(actionType) {
    const icons = {
        'email_send': 'fas fa-envelope',
        'whatsapp_reply': 'fab fa-whatsapp',
        'payment_processed': 'fas fa-credit-card',
        'social_post': 'fas fa-share-alt',
        'audit_completed': 'fas fa-chart-bar'
    };
    return icons[actionType] || 'fas fa-cog';
}

function getActivityColor(actionType) {
    const colors = {
        'email_send': '#2563eb',
        'whatsapp_reply': '#25d366',
        'payment_processed': '#10b981',
        'social_post': '#0077b5',
        'audit_completed': '#f59e0b'
    };
    return colors[actionType] || '#6b7280';
}

function getSampleActivities() {
    return [
        {
            id: 1,
            type: 'email',
            title: 'System initialized',
            description: 'AI Employee started successfully',
            time: new Date().toLocaleTimeString(),
            icon: 'fas fa-rocket',
            iconColor: '#10b981'
        }
    ];
}

function parseFrontmatter(content) {
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatterMatch) return {};
    
    const frontmatter = {};
    const lines = frontmatterMatch[1].split('\n');
    
    lines.forEach(line => {
        const [key, ...valueParts] = line.split(':');
        if (key && valueParts.length) {
            frontmatter[key.trim()] = valueParts.join(':').trim();
        }
    });
    
    return frontmatter;
}

async function updateApprovalStatus(approvalId, action) {
    const pendingDir = path.join(VAULT_PATH, 'Pending_Approval');
    const approvedDir = path.join(VAULT_PATH, 'Approved');
    const rejectedDir = path.join(VAULT_PATH, 'Rejected');
    
    const files = await fs.readdir(pendingDir);
    const approvalFile = files.find(f => f.includes(approvalId.toString()));
    
    if (approvalFile) {
        const sourcePath = path.join(pendingDir, approvalFile);
        let destDir = action === 'approve' ? approvedDir : rejectedDir;
        
        // Ensure destination directory exists
        await fs.mkdir(destDir, { recursive: true });
        
        const destPath = path.join(destDir, approvalFile);
        await fs.rename(sourcePath, destPath);
        
        // Update file content
        const content = await fs.readFile(destPath, 'utf-8');
        const updatedContent = content.replace(
            /status: pending/,
            `status: ${action}d\napproved_at: ${new Date().toISOString()}`
        );
        await fs.writeFile(destPath, updatedContent);
    }
}

async function executeApprovedAction(approvalId) {
    // This would trigger the actual action via MCP servers
    logger.info(`Executing approved action ${approvalId}`);
    // Implementation depends on the specific action
}

async function logAction(logEntry) {
    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(VAULT_PATH, 'Logs', `${today}.json`);
    
    let logs = [];
    try {
        const content = await fs.readFile(logFile, 'utf-8');
        logs = JSON.parse(content);
    } catch {
        // File doesn't exist yet
    }
    
    logs.push(logEntry);
    await fs.writeFile(logFile, JSON.stringify(logs, null, 2));
}

async function processEmails() {
    logger.info('Processing emails...');
    // Implement email processing logic
}

async function processWhatsApp() {
    logger.info('Processing WhatsApp messages...');
    // Implement WhatsApp processing logic
}

async function runBusinessAudit() {
    logger.info('Running business audit...');
    // Implement audit logic
}

async function generateReport() {
    logger.info('Generating report...');
    // Implement report generation logic
}

function getDefaultDashboardData() {
    return {
        aiActive: true,
        pendingApprovals: [],
        recentActivities: getSampleActivities(),
        stats: {
            weeklyRevenue: 2450,
            pendingTasks: 8,
            unreadMessages: 5,
            aiUptime: 99.8
        },
        dashboardContent: getDashboardTemplate()
    };
}

// WebSocket for real-time updates
const wss = new WebSocketServer({ port: 8080 });
const clients = new Set();

wss.on('connection', (ws) => {
    clients.add(ws);
    logger.info('New WebSocket connection');
    
    ws.on('message', (message) => {
        logger.info('WebSocket message:', message.toString());
        // Handle incoming messages
    });
    
    ws.on('close', () => {
        clients.delete(ws);
        logger.info('WebSocket disconnected');
    });
});

// Broadcast updates to all clients
function broadcastUpdate(data) {
    const message = JSON.stringify(data);
    clients.forEach(client => {
        if (client.readyState === 1) {
            client.send(message);
        }
    });
}

// Scheduled tasks
cron.schedule('0 8 * * 1', async () => {
    // Every Monday at 8 AM
    logger.info('Running weekly business audit...');
    await runBusinessAudit();
    
    broadcastUpdate({
        type: 'audit_completed',
        message: 'Weekly audit completed',
        timestamp: new Date().toISOString()
    });
});

cron.schedule('*/5 * * * *', async () => {
    // Every 5 minutes
    logger.info('Checking for new tasks...');
    // Check Needs_Action folder and process
    
    broadcastUpdate({
        type: 'status_update',
        timestamp: new Date().toISOString(),
        status: 'active'
    });
});

// Start server
async function startServer() {
    await initVault();
    
    app.listen(PORT, () => {
        logger.info(`Server running on http://localhost:${PORT}`);
        logger.info(`WebSocket server on ws://localhost:8080`);
        logger.info('AI Employee system initialized');
    });
}

// Handle graceful shutdown
process.on('SIGTERM', async () => {
    logger.info('SIGTERM received, shutting down gracefully...');
    
    // Close WebSocket connections
    wss.close();
    
    // Save current state
    await saveSystemState();
    
    process.exit(0);
});

async function saveSystemState() {
    const state = {
        lastShutdown: new Date().toISOString(),
        stats: await getDashboardData()
    };
    
    const statePath = path.join(VAULT_PATH, 'Logs', 'system_state.json');
    await fs.writeFile(statePath, JSON.stringify(state, null, 2));
    logger.info('System state saved');
}

startServer().catch(error => {
    logger.error('Failed to start server:', error);
    process.exit(1);
});