#!/usr/bin/env python3
"""
Scheduler that runs popup_review.py and then schedules quiz_review.py to run every 4 hours.

This script:
1. Executes popup_review.py and waits for it to complete
2. Starts an APScheduler that runs quiz_review.py every 4 hours
3. Runs indefinitely, allowing quiz_review.py to execute on schedule

Usage:
    uv run python schedule_quiz_runner.py
    
Or configure it to run at system startup via Windows Task Scheduler.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
import json

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.schedulers.base import SchedulerAlreadyRunningError
    from apscheduler.events import EVENT_JOB_EXECUTED
except ImportError:
    print("Error: apscheduler is not installed.")
    print("Install it with: uv pip install apscheduler")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schedule_quiz_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Get project root
PROJECT_ROOT = Path(__file__).parent
POPUP_REVIEW_SCRIPT = PROJECT_ROOT / "popup_review.py"
QUIZ_REVIEW_SCRIPT = PROJECT_ROOT / "quiz_review.py"
QUIZ_HISTORY_FILE = PROJECT_ROOT / "quiz_history.json"

# Scheduler state
scheduler_instance = None
quiz_execution_count = 0
MAX_QUIZ_EXECUTIONS = 3
QUIZ_INTERVAL_HOURS = 4


def load_quiz_history():
    """
    Load quiz execution history from quiz_history.json.
    
    Returns:
        dict: Quiz history with 'executions' list, 'last_execution_counter', and 'last_execution_timestamp'
    """
    if QUIZ_HISTORY_FILE.exists():
        try:
            with open(QUIZ_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading quiz_history.json: {e}")
    
    return {"executions": [], "last_execution_counter": 0, "last_execution_timestamp": None}


def save_quiz_history(history):
    """
    Save quiz execution history to quiz_history.json.
    
    Args:
        history (dict): Quiz history data to save
    """
    try:
        with open(QUIZ_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving quiz_history.json: {e}")


def record_quiz_execution(counter):
    """
    Record a quiz_review.py execution in the history file.
    
    Args:
        counter (int): Execution counter number
    """
    history = load_quiz_history()
    timestamp = datetime.now().isoformat()
    
    history["executions"].append({
        "counter": counter,
        "timestamp": timestamp
    })
    history["last_execution_counter"] = counter
    history["last_execution_timestamp"] = timestamp
    
    save_quiz_history(history)
    logger.info(f"Recorded quiz execution #{counter} at {timestamp}")


def calculate_missed_executions():
    """
    Calculate how many quiz executions are missing due to device shutdowns.
    
    Returns:
        tuple: (missed_count, minutes_until_next_execution)
               - missed_count: Number of 4-hour intervals that have passed
               - minutes_until_next: Minutes until next execution (0 if should run immediately)
    """
    history = load_quiz_history()
    
    # No history - this is the first run
    if not history["last_execution_timestamp"]:
        logger.info("No quiz execution history found. Starting fresh.")
        return 0, 0
    
    try:
        last_exec = datetime.fromisoformat(history["last_execution_timestamp"])
    except (ValueError, TypeError):
        logger.warning("Invalid timestamp in quiz_history.json. Resetting.")
        return 0, 0
    
    now = datetime.now()
    time_elapsed = now - last_exec
    total_minutes_elapsed = time_elapsed.total_seconds() / 60
    interval_minutes = QUIZ_INTERVAL_HOURS * 60
    
    # Calculate how many complete intervals have passed
    missed_count = int(total_minutes_elapsed // interval_minutes)
    
    if missed_count > 0:
        logger.info(f"Detected {missed_count} missed execution(s) (last execution was {total_minutes_elapsed:.0f} minutes ago)")
        return missed_count, 0  # Execute immediately
    
    # Calculate minutes until next execution
    minutes_until_next = interval_minutes - (total_minutes_elapsed % interval_minutes)
    logger.info(f"Next quiz execution in {minutes_until_next:.0f} minutes")
    
    return 0, int(minutes_until_next)


def should_reset_daily_counter():
    """
    Check if daily execution counter should be reset due to day change.
    
    Returns:
        True if last execution was on a different day, False otherwise
    """
    history = load_quiz_history()
    
    if not history["last_execution_timestamp"]:
        return False
    
    try:
        last_exec = datetime.fromisoformat(history["last_execution_timestamp"])
        today = datetime.now()
        
        # Check if last execution was on a different day
        if last_exec.date() != today.date():
            logger.info(f"Last execution was on {last_exec.date()}, today is {today.date()}. Resetting daily counter.")
            return True
    except (ValueError, TypeError):
        return False
    
    return False


def should_exit_scheduler():
    """
    Determine if the scheduler should exit.
    
    Returns:
        True if max executions reached, False otherwise
    """
    return quiz_execution_count >= MAX_QUIZ_EXECUTIONS


def on_scheduler_event(event):
    """
    Handle scheduler events to gracefully exit when jobs are removed.
    
    Args:
        event: APScheduler event object
    """
    global scheduler_instance
    
    if scheduler_instance and scheduler_instance.running:
        # Check if there are any remaining jobs
        if len(scheduler_instance.get_jobs()) == 0:
            logger.info("No more jobs scheduled. Exiting scheduler.")
            try:
                scheduler_instance.shutdown(wait=False)
            except Exception as e:
                logger.warning(f"Error during scheduler shutdown: {e}")



def daily_review_file_exists():
    """
    Check if daily review JSON file already exists for today.
    
    The daily file format is: review_{YYYY-MM-DD}.json
    This prevents running popup_review.py multiple times on the same day.
    
    Returns:
        True if daily review file exists, False otherwise
    """
    today = datetime.now().strftime("%Y-%m-%d")
    daily_filename = PROJECT_ROOT / f"review_{today}.json"
    
    if daily_filename.exists():
        logger.info(f"Daily review file already exists: {daily_filename.name}")
        return True
    
    return False


def run_popup_review():
    """Execute popup_review.py only if no daily review file exists yet."""
    # Check if daily review file already exists
    if daily_review_file_exists():
        logger.info("Skipping popup_review.py - daily review already collected on first login")
        return True
    
    logger.info("Starting popup_review.py...")
    
    if not POPUP_REVIEW_SCRIPT.exists():
        logger.error(f"popup_review.py not found at {POPUP_REVIEW_SCRIPT}")
        return False
    
    try:
        # Run popup_review.py and wait for it to complete
        time.sleep(60)

        result = subprocess.run(
            [sys.executable, str(POPUP_REVIEW_SCRIPT)],
            cwd=PROJECT_ROOT,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("popup_review.py completed successfully")
            return True
        else:
            logger.error(f"popup_review.py exited with code {result.returncode}")
            return False
    except Exception as e:
        logger.error(f"Error running popup_review.py: {e}")
        return False


def run_quiz_review():
    """Execute quiz_review.py and record execution in history."""
    global quiz_execution_count, scheduler_instance
    
    quiz_execution_count += 1
    logger.info(f"Running scheduled quiz_review.py... (execution {quiz_execution_count}/{MAX_QUIZ_EXECUTIONS})")
    
    if not QUIZ_REVIEW_SCRIPT.exists():
        logger.error(f"quiz_review.py not found at {QUIZ_REVIEW_SCRIPT}")
        return
    
    try:
        # Run quiz_review.py in a subprocess and capture output
        result = subprocess.run(
            [sys.executable, str(QUIZ_REVIEW_SCRIPT)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=1200  # 20-minute timeout
        )
        
        if result.returncode == 0:
            logger.info("quiz_review.py completed successfully")
        else:
            logger.error(f"quiz_review.py exited with code {result.returncode}")
            if result.stderr:
                logger.error(f"stderr: {result.stderr}")
            if result.stdout:
                logger.info(f"stdout: {result.stdout}")
        
        # Record this execution in history
        record_quiz_execution(quiz_execution_count)
        
    except subprocess.TimeoutExpired:
        logger.error("quiz_review.py timed out after 20 minutes")
    except Exception as e:
        logger.error(f"Error running quiz_review.py: {e}")
    
    # Check if we've reached the maximum executions
    if quiz_execution_count >= MAX_QUIZ_EXECUTIONS:
        logger.info(f"Reached maximum of {MAX_QUIZ_EXECUTIONS} quiz executions. Removing scheduled job.")
        if scheduler_instance and scheduler_instance.running:
            try:
                scheduler_instance.remove_job('quiz_review_job')
                logger.info("Scheduled job removed successfully. Scheduler will exit.")
            except Exception as e:
                logger.warning(f"Could not remove job: {e}")


def main():
    """Main entry point."""
    global scheduler_instance, quiz_execution_count
    
    logger.info("=" * 60)
    logger.info("Quiz Scheduler Started")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info("=" * 60)
    
    # Step 1: Run popup_review.py first
    logger.info("\nStep 1: Running popup_review.py...")
    if not run_popup_review():
        logger.error("Failed to run popup_review.py. Exiting.")
        sys.exit(1)
    
    # Step 2: Check for missed executions due to device shutdown
    logger.info("\nStep 2: Checking for missed quiz executions...")
    missed_executions, minutes_until_next = calculate_missed_executions()
    
    history = load_quiz_history()
    quiz_execution_count = history["last_execution_counter"]
    
    # Reset daily counter if last execution was on a different day
    if should_reset_daily_counter():
        logger.info("Daily counter reset for new day.")
        quiz_execution_count = 0
    
    if missed_executions > 0:
        logger.warning(f"Device was offline. {missed_executions} quiz execution(s) were missed.")
        
        # Execute first review immediately
        if quiz_execution_count >= MAX_QUIZ_EXECUTIONS:
            logger.info(f"Reached maximum of {MAX_QUIZ_EXECUTIONS} quiz executions. Not executing missed ones.")

        else:
            logger.info(f"Running missed quiz...")
            run_quiz_review()
            time.sleep(2)  # Brief delay

            
    
    # Step 3: Schedule quiz_review.py to run every 4 hours (3 times maximum)
    logger.info("\nStep 3: Scheduling quiz_review.py to run every 4 hours (3 executions over 12 hours)...")
    
    try:
        scheduler = BlockingScheduler()
        scheduler_instance = scheduler
        
        # Add event listener to gracefully exit when jobs are removed
        scheduler.add_listener(on_scheduler_event)
        
        # Determine initial delay
        if quiz_execution_count >= MAX_QUIZ_EXECUTIONS:
            logger.info(f"Maximum executions ({MAX_QUIZ_EXECUTIONS}) already reached. Scheduler will not run further executions.")
            logger.info("Exiting.")
            sys.exit(0)
        
        # Add job to run quiz_review.py every 4 hours
        scheduler.add_job(
            run_quiz_review,
            trigger=IntervalTrigger(hours=QUIZ_INTERVAL_HOURS),
            id='quiz_review_job',
            name='Quiz Review Every 4 Hours',
            replace_existing=True
        )
        
        logger.info(f"Scheduler started. quiz_review.py will run {MAX_QUIZ_EXECUTIONS - quiz_execution_count} more time(s) at 4-hour intervals.")
        logger.info("Press Ctrl+C to stop the scheduler.")
        
        # This blocks indefinitely, running the scheduler
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
