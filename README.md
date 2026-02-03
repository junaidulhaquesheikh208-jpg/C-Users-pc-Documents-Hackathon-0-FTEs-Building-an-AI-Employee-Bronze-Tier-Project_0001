# Personal AI Employee

This project implements a Personal AI Employee that manages your personal and business affairs 24/7 using Claude Code, Obsidian, and MCP servers.

## Architecture

The system consists of several components:

- **Perception Layer**: Watcher scripts that monitor Gmail, WhatsApp, and file systems
- **Reasoning Layer**: Claude Code as the AI reasoning engine
- **Action Layer**: MCP servers for external actions (email, browser automation, social media, etc.)
- **Memory Layer**: Obsidian vault for persistent storage and dashboard
- **Orchestration Layer**: Python scripts to coordinate all components
- **Monitoring Layer**: Watchdog processes to ensure system reliability

## Components

### Watchers
- `gmail_watcher.py`: Monitors Gmail for important/unread emails
- `whatsapp_watcher.py`: Monitors WhatsApp for urgent messages
- `filesystem_watcher.py`: Monitors a designated folder for new files
- `base_watcher.py`: Abstract base class for all watchers

### MCP Servers
- `linkedin_poster.py`: Handles LinkedIn posting and scheduling
- `.claude/mcp.json`: Configuration for Model Context Protocol servers

### Orchestration & Monitoring
- `orchestrator.py`: Main orchestrator that coordinates all components
- `watchdog.py`: Monitors and restarts critical processes
- `audit_logic.py`: Business intelligence and financial analysis
- `retry_handler.py`: Robust retry mechanisms for transient failures

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Obsidian vault:
   - Open the `AI_Employee_Vault` directory as a vault in Obsidian
   - Review and customize `Company_Handbook.md` with your rules

3. Configure Claude Code:
   - Ensure Claude Code is installed and configured
   - Set up MCP servers as defined in `.claude/mcp.json`

4. Set up Gmail API (optional):
   - Follow Google's instructions to get credentials
   - Place credentials in the location specified in the config

5. Set up WhatsApp Web (optional):
   - Configure Playwright for WhatsApp Web automation
   - Note: Be aware of WhatsApp's terms of service

6. Set up LinkedIn API (optional):
   - Obtain LinkedIn API credentials for posting capabilities

7. Run the orchestrator:
```bash
python orchestrator.py
```

For production use, also run the watchdog:
```bash
python watchdog.py
```

## Silver Tier Capabilities

This implementation includes all Bronze Tier features plus:

- **Multi-channel monitoring**: Gmail, WhatsApp, and file system monitoring
- **LinkedIn integration**: Automated posting and scheduling capabilities
- **Business intelligence**: Weekly CEO briefings with revenue and bottleneck analysis
- **Robust operations**: Retry logic and error handling
- **Process monitoring**: Watchdog to ensure system reliability
- **Human-in-the-loop**: Sophisticated approval workflows

## Security

- Store sensitive credentials in `.env` file (not committed to version control)
- Use human-in-the-loop approval for sensitive actions
- All logs are stored locally for audit purposes
- Dry-run mode available for testing

## Folder Structure

- `/Inbox` - Incoming items to process
- `/Needs_Action` - Items requiring action
- `/Plans` - Plans created by Claude
- `/Pending_Approval` - Actions awaiting human approval
- `/Done` - Completed tasks
- `/Logs` - System logs
- `/Briefings` - Weekly CEO briefings and daily status reports
- `/Accounting` - Financial records and transactions

## Human-in-the-Loop

For sensitive actions (payments, important emails, social media posts), the system creates approval files in the `/Pending_Approval` folder. Move these to `/Approved` to authorize the action, or `/Rejected` to deny it.

## Scheduling

The system includes automated scheduling for:
- Daily status reports at 8 AM
- Weekly CEO briefings on Sundays at 7 AM
- Custom scheduling for social media posts