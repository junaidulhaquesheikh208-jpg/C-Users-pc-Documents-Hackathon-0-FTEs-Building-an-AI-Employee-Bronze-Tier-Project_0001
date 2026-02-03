import subprocess
import time
import logging
from pathlib import Path
import psutil
import os
from datetime import datetime


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


PROCESSES = {
    'orchestrator': {
        'cmd': ['python', 'orchestrator.py'],
        'restart_cmd': ['python', 'orchestrator.py'],
        'working_dir': '.',
        'auto_restart': True
    },
    'gmail_watcher': {
        'cmd': ['python', 'Watchers/gmail_watcher.py'],
        'restart_cmd': ['python', 'Watchers/gmail_watcher.py'],
        'working_dir': '.',
        'auto_restart': True
    },
    'whatsapp_watcher': {
        'cmd': ['python', 'Watchers/whatsapp_watcher.py'],
        'restart_cmd': ['python', 'Watchers/whatsapp_watcher.py'],
        'working_dir': '.',
        'auto_restart': True
    },
    'filesystem_watcher': {
        'cmd': ['python', 'Watchers/filesystem_watcher.py'],
        'restart_cmd': ['python', 'Watchers/filesystem_watcher.py'],
        'working_dir': '.',
        'auto_restart': True
    }
}


def is_process_running(process_info):
    """Check if a process is currently running"""
    try:
        # Search for processes with matching command
        for proc in psutil.process_iter(['pid', 'cmdline', 'status']):
            try:
                cmdline = ' '.join(proc.info['cmdline'])
                if all(arg in cmdline for arg in process_info['cmd']):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    except Exception as e:
        logger.error(f"Error checking process: {e}")
        return None


def start_process(name, process_info):
    """Start a process"""
    try:
        os.chdir(process_info['working_dir'])
        proc = subprocess.Popen(
            process_info['restart_cmd'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Started {name} with PID {proc.pid}")
        return proc
    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")
        return None


def notify_human(message):
    """Notify human operator of important events"""
    logger.warning(f"ALERT: {message}")
    # In a real implementation, this might send an email, SMS, or other notification
    # For now, we'll just log it


def check_and_restart():
    """Check all processes and restart any that are not running"""
    for name, info in PROCESSES.items():
        running_proc = is_process_running(info)
        
        if running_proc:
            logger.debug(f"{name} is running (PID: {running_proc.pid})")
        else:
            logger.warning(f"{name} is not running")
            
            if info['auto_restart']:
                logger.info(f"Attempting to restart {name}...")
                new_proc = start_process(name, info)
                
                if new_proc:
                    logger.info(f"Successfully restarted {name}")
                else:
                    logger.error(f"Failed to restart {name}")
                    notify_human(f"CRITICAL: Failed to restart {name}")
            else:
                logger.info(f"{name} is not set to auto-restart")
                notify_human(f"Process {name} is down and not auto-restarting")


def main():
    """Main watchdog loop"""
    logger.info("Starting AI Employee Watchdog Service")
    logger.info("Monitoring processes: " + ", ".join(PROCESSES.keys()))
    
    try:
        while True:
            check_and_restart()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Watchdog service stopped by user")
    except Exception as e:
        logger.error(f"Watchdog service error: {e}")
        notify_human(f"Watchdog service crashed: {e}")


if __name__ == "__main__":
    main()