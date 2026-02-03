import os
import sys
import time
import logging
from pathlib import Path
import subprocess
from threading import Thread
import signal
import json
from datetime import datetime, timedelta
sys.path.append(".")  # Add current directory to path to import audit_logic
from audit_logic import generate_ceo_briefing_data, format_briefing_markdown


class Orchestrator:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.approved = self.vault_path / 'Pending_Approval'
        self.plans = self.vault_path / 'Plans'
        self.briefings = self.vault_path / 'Briefings'
        self.accounting = self.vault_path / 'Accounting'
        self.logger = self.setup_logging()

    def setup_logging(self):
        """Set up logging for the orchestrator"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.vault_path / 'Logs' / f'orchestrator_{time.strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger('Orchestrator')

    def start_watchers(self):
        """Start all watcher processes"""
        self.logger.info("Starting watchers...")

        # Import watchers here to avoid circular dependencies
        try:
            from Watchers.gmail_watcher import GmailWatcher
            from Watchers.filesystem_watcher import FileSystemWatcher
            from Watchers.whatsapp_watcher import WhatsAppWatcher

            # Start Gmail watcher in a separate thread
            gmail_watcher = GmailWatcher(
                vault_path=str(self.vault_path),
                credentials_path="./gmail_credentials.json"
            )
            gmail_thread = Thread(target=gmail_watcher.run, daemon=True)
            gmail_thread.start()
            self.logger.info("Gmail watcher started")
        except ImportError as e:
            self.logger.warning(f"Gmail watcher not available: {e}")

        # Start file system watcher in a separate thread
        try:
            fs_watcher = FileSystemWatcher(
                vault_path=str(self.vault_path),
                drop_folder="./Drop_Folder"
            )
            fs_thread = Thread(target=fs_watcher.start, daemon=True)
            fs_thread.start()
            self.logger.info("File system watcher started")
        except ImportError as e:
            self.logger.warning(f"File system watcher not available: {e}")

        # Start WhatsApp watcher in a separate thread
        try:
            whatsapp_watcher = WhatsAppWatcher(
                vault_path=str(self.vault_path),
                session_path="./whatsapp_session"
            )
            whatsapp_thread = Thread(target=whatsapp_watcher.run, daemon=True)
            whatsapp_thread.start()
            self.logger.info("WhatsApp watcher started")
        except ImportError as e:
            self.logger.warning(f"WhatsApp watcher not available: {e}")

    def process_needs_action(self):
        """Process files in the Needs_Action folder"""
        self.logger.info("Checking for files in Needs_Action...")

        needs_action_files = list(self.needs_action.glob("*.md"))
        if not needs_action_files:
            self.logger.info("No files in Needs_Action")
            return

        for file_path in needs_action_files:
            self.logger.info(f"Processing file: {file_path.name}")

            # Create a plan file for Claude to process
            plan_file = self.create_plan(file_path)

            # Move the original file to Done once processed
            done_path = self.done / file_path.name
            file_path.rename(done_path)
            self.logger.info(f"Moved {file_path.name} to Done")

    def create_plan(self, action_file: Path):
        """Create a plan file for Claude to process"""
        # Read the action file
        with open(action_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create a plan file
        plan_filename = f"PLAN_{action_file.stem}_{int(time.time())}.md"
        plan_path = self.plans / plan_filename

        # Basic plan structure
        plan_content = f"""---
created: {time.strftime('%Y-%m-%dT%H:%M:%S')}
status: pending
original_file: {action_file.name}
---

# Plan for {action_file.stem}

## Objective
Process the action requested in {action_file.name}

## Original Content
{content}

## Steps
- [ ] Analyze the request
- [ ] Determine appropriate action
- [ ] Execute action (if approved)
- [ ] Log results
- [ ] Mark as complete

## Approval Required
Some actions may require human approval. Check Pending_Approval folder.
"""

        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(plan_content)

        self.logger.info(f"Created plan file: {plan_path.name}")
        return plan_path

    def check_approvals(self):
        """Check for approved files and execute actions"""
        self.logger.info("Checking for approved files...")

        # Look for files that have been moved to approved
        approved_dir = self.vault_path / 'Approved'
        if not approved_dir.exists():
            approved_dir.mkdir(exist_ok=True)

        # Also check for files in Pending_Approval that might have been approved
        pending_approval_dir = self.vault_path / 'Pending_Approval'
        if not pending_approval_dir.exists():
            pending_approval_dir.mkdir(exist_ok=True)

        # Process any files that were approved (moved to Approved folder)
        approved_files = list(approved_dir.glob("*.md"))
        for file_path in approved_files:
            self.execute_approved_action(file_path)

    def execute_approved_action(self, approval_file: Path):
        """Execute an action that has been approved"""
        self.logger.info(f"Executing approved action: {approval_file.name}")

        # In a real implementation, this would call the appropriate MCP server
        # based on the action type specified in the file
        # For now, we'll just log the action and move it to Done

        # Move to done after execution
        done_path = self.done / approval_file.name
        approval_file.rename(done_path)
        self.logger.info(f"Completed approved action: {approval_file.name}")

    def update_dashboard(self):
        """Update the dashboard with current status"""
        dashboard_path = self.vault_path / 'Dashboard.md'

        # Count files in various folders
        needs_action_count = len(list(self.needs_action.glob("*.md")))
        pending_approval_count = len(list((self.vault_path / 'Pending_Approval').glob("*.md")))
        done_count = len(list(self.done.glob("*.md")))
        plans_count = len(list(self.plans.glob("*.md")))

        # Read current dashboard
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update the status section
        import re
        content = re.sub(
            r'- \*\*Pending Actions\*\*: \d+',
            f'- **Pending Actions**: {needs_action_count}',
            content
        )

        # Update other counts if they exist in the dashboard
        content = re.sub(
            r'- \*\*Active Watchers\*\*: \d+',
            f'- **Active Watchers**: 3',  # Assuming all 3 watchers are active
            content
        )

        # Write updated dashboard
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info("Dashboard updated")

    def run_scheduler(self):
        """Run scheduled tasks"""
        current_time = datetime.now()

        # Weekly CEO Briefing: Every Sunday at 7 AM
        if current_time.weekday() == 6 and current_time.hour == 7 and current_time.minute < 5:  # Sunday at 7 AM
            self.generate_weekly_briefing()

        # Daily status check: Every day at 8 AM
        if current_time.hour == 8 and current_time.minute < 5:
            self.generate_daily_status()

    def generate_weekly_briefing(self):
        """Generate the weekly CEO briefing"""
        self.logger.info("Generating weekly CEO briefing...")

        # Calculate the date range for the week
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)  # Sunday

        start_date = start_of_week.strftime('%Y-%m-%d')
        end_date = end_of_week.strftime('%Y-%m-%d')
        briefing_date = today.strftime('%Y-%m-%d')

        # Generate briefing data using audit logic
        briefing_data = generate_ceo_briefing_data(start_of_week, end_of_week)
        briefing_content = format_briefing_markdown(briefing_data)

        # Create briefing file
        briefing_path = self.briefings / f'{briefing_date}_Weekly_Briefing.md'

        with open(briefing_path, 'w', encoding='utf-8') as f:
            f.write(briefing_content)

        self.logger.info(f"Weekly briefing generated: {briefing_path.name}")

    def generate_daily_status(self):
        """Generate a daily status update"""
        self.logger.info("Generating daily status...")

        # Count items in various folders
        needs_action_count = len(list(self.needs_action.glob("*.md")))
        pending_approval_count = len(list((self.vault_path / 'Pending_Approval').glob("*.md")))

        # Create daily status file
        status_date = datetime.now().strftime('%Y-%m-%d')
        status_path = self.vault_path / 'Briefings' / f'{status_date}_Daily_Status.md'

        status_content = f"""# Daily Status Report - {status_date}

---
generated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
---

## Today's Overview
- **Pending Actions**: {needs_action_count}
- **Pending Approvals**: {pending_approval_count}
- **System Status**: Operational

## Recent Activity
- System monitoring active
- Watchers operational

---
*Generated by AI Employee v0.1*
"""

        with open(status_path, 'w', encoding='utf-8') as f:
            f.write(status_content)

        self.logger.info(f"Daily status generated: {status_path.name}")

    def count_completed_tasks(self, start_date, end_date):
        """Count completed tasks within a date range"""
        # This would normally analyze the /Done folder for tasks completed in the date range
        # For now, returning a placeholder
        done_files = list(self.done.glob("*.md"))
        return f"- {len(done_files)} tasks completed this week\n"

    def get_weekly_revenue(self, start_date, end_date):
        """Get revenue for the week (placeholder implementation)"""
        # This would normally integrate with accounting system
        # For now, returning a placeholder
        return 1250.00  # Placeholder revenue

    def run(self):
        """Main orchestrator loop"""
        self.logger.info("Starting AI Employee Orchestrator...")
        self.start_watchers()

        def signal_handler(sig, frame):
            self.logger.info("Shutting down orchestrator...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while True:
                # Process any pending actions
                self.process_needs_action()

                # Check for approvals
                self.check_approvals()

                # Update dashboard
                self.update_dashboard()

                # Run scheduler
                self.run_scheduler()

                # Sleep before next iteration
                time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            self.logger.info("Orchestrator interrupted by user")
        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")


if __name__ == "__main__":
    # Initialize and run the orchestrator
    orchestrator = Orchestrator(vault_path="./AI_Employee_Vault")
    orchestrator.run()