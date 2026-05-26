# Quiz Review Scheduler Setup Guide

This guide explains how to schedule the quiz review system to run automatically on your computer.

## Overview

The scheduler system consists of:
- **popup_review.py**: GUI app that collects topics to review
- **quiz_review.py**: Quiz app that tests knowledge on collected topics
- **schedule_quiz_runner.py**: Main scheduler that orchestrates the workflow

### Workflow

1. At system startup, `schedule_quiz_runner.py` is launched
2. It immediately runs `popup_review.py` and waits for it to complete
3. Once `popup_review.py` finishes, it starts a background scheduler
4. The scheduler runs `quiz_review.py` every 4 hours indefinitely
5. All activity is logged to `schedule_quiz_runner.log`

## Prerequisites

- Python 3.12 or later
- `uv` package manager installed
- Windows OS with Task Scheduler
- Administrator privileges for initial setup

### Install uv

If you don't have `uv` installed, download it from:
https://docs.astral.sh/uv/getting-started/installation/

Or install via PowerShell (admin):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install Dependencies

The required Python packages are listed in `pyproject.toml`. Run:

```bash
uv sync
```

This installs:
- pandas
- python-dotenv
- requests
- apscheduler

## Setup Methods

### Method 1: PowerShell (Recommended)

1. Open PowerShell as Administrator
2. Navigate to the project directory
3. Run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
.\schedule_quiz_at_startup.ps1
```

To remove the task later:
```powershell
.\schedule_quiz_at_startup.ps1 -RemoveOnly
```

### Method 2: Batch File (Windows Command Prompt)

1. Open Command Prompt as Administrator
2. Navigate to the project directory
3. Run:

```cmd
schedule_quiz_at_startup.bat
```

To remove the task later:
```cmd
schedule_quiz_at_startup.bat /remove
```

### Method 3: Manual Setup via Task Scheduler GUI

1. Open Task Scheduler (Win+R → `taskschd.msc`)
2. Click "Create Basic Task..." on the right
3. Configure:
   - **Name**: Quiz Review Scheduler
   - **Trigger**: At startup
   - **Action**: Start a program
   - **Program/script**: `powershell.exe`
   - **Arguments**: `-WindowStyle Hidden -NoProfile -Command "& uv run python 'C:\Path\To\schedule_quiz_runner.py'"`
   - **Start in**: `C:\Path\To\Project\Root`
4. Check "Run with highest privileges"
5. Click Finish

## Usage

### Run Manually

If you want to test or run the scheduler manually without setting up Task Scheduler:

```bash
uv run python schedule_quiz_runner.py
```

The script will:
1. Launch `popup_review.py` (GUI window will appear)
2. Wait for you to finish entering topics
3. Start the 4-hour scheduler for `quiz_review.py`
4. Run indefinitely (press Ctrl+C to stop)

### View Logs

The scheduler logs all activity to `schedule_quiz_runner.log`:

```bash
tail -f schedule_quiz_runner.log
```

Or open the file in any text editor to view the history.

## Troubleshooting

### Task doesn't run at startup
- Check that Task Scheduler shows "Last Run Result: The task completed with an exit code of (0)."
- Ensure "Run with highest privileges" is enabled
- Check that `uv` is in your system PATH
- Review `schedule_quiz_runner.log` for errors

### "uv not found" error
- Verify `uv` is installed: `uv --version`
- Ensure `uv` is in your PATH:
  - Open Command Prompt and type: `where uv`
  - If not found, reinstall `uv` and ensure to add it to PATH

### Dependencies not installed
- Run: `uv sync` in the project directory
- Check the log file for specific import errors

### popup_review.py doesn't launch
- Check that `popup_review.py` exists and is readable
- Verify all dependencies in `popup_review.py` are installed
- Check the log file for specific errors

### Quiz doesn't run every 4 hours
- Ensure the scheduler process is still running (check Task Manager)
- Review `schedule_quiz_runner.log` for errors
- If scheduler crashed, you'll need to restart it manually or via a reboot

## Advanced Configuration

### Change the Quiz Interval

Edit `schedule_quiz_runner.py` and find this line:

```python
scheduler.add_job(
    run_quiz_review,
    trigger=IntervalTrigger(hours=4),  # Change this value
    ...
)
```

Change `hours=4` to desired interval:
- Every 2 hours: `hours=2`
- Every 30 minutes: `minutes=30`
- Every day: `days=1`

### Change Task Trigger

Instead of "At startup", you can trigger the task at a specific time. In the PowerShell script or Task Scheduler GUI, modify the trigger to:
- At a specific time each day
- On a schedule
- On an event

## Removing the Task

### PowerShell:
```powershell
.\schedule_quiz_at_startup.ps1 -RemoveOnly
```

### Batch:
```cmd
schedule_quiz_at_startup.bat /remove
```

### Task Scheduler GUI:
1. Open Task Scheduler
2. Find "Quiz Review Scheduler"
3. Right-click → Delete

## File Structure

```
project/
├── popup_review.py                 # Topic collection GUI
├── quiz_review.py                  # Quiz application
├── schedule_quiz_runner.py          # Main scheduler script
├── schedule_quiz_at_startup.ps1     # PowerShell setup script
├── schedule_quiz_at_startup.bat     # Batch setup script
├── schedule_quiz_at_startup_GUIDE.md # This file
├── schedule_quiz_runner.log         # Generated log file
├── pyproject.toml                   # Python dependencies
└── README.md                        # Project README
```

## Notes

- The scheduler keeps `schedule_quiz_runner.py` running as a background process
- The process uses APScheduler's `BlockingScheduler`, which efficiently manages scheduled tasks
- Log files are appended to (they grow over time - consider archiving old logs)
- The hidden PowerShell window prevents the scheduler from appearing in the taskbar

## Support

If you encounter issues:
1. Check `schedule_quiz_runner.log` for detailed error messages
2. Run the scheduler manually with `uv run python schedule_quiz_runner.py` to see output
3. Verify all files exist and have correct paths
4. Ensure proper file permissions and PATH configuration
