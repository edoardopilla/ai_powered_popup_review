# AI-powered Quiz Review Scheduler

A desktop application that helps you review topics through interactive quizzes. This system generates AI-powered quiz questions based on topics you want to review and allows you to practice them on a schedule.

## Features

- **Interactive Popup Window**: Quickly enter topics you want to review
- **AI-Generated Questions**: Automatically generates quiz questions using OpenAI-compatible APIs
- **Quiz Application**: Practice questions with a clean, user-friendly interface
- **Scheduled Execution**: Automatically run quizzes every 4 hours
- **Windows Task Scheduler Integration**: Set up the system to run at startup
- **Progress Tracking**: View statistics and history of quiz sessions
- **Response Logging**: All quiz responses and AI-generated solutions are saved to JSON files

## Prerequisites

- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Windows OS** (for Task Scheduler integration)
- **OpenAI API Key** (or compatible LLM API endpoint)
- Administrator privileges (for Task Scheduler setup)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai_powered_popup_review
   ```

2. **Install dependencies** using `uv`:
   ```bash
   uv sync
   ```

3. **Configure API credentials**:
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_api_key_here
   OPENAI_API_ENDPOINT=https://api.openai.com/v1
   ```
   
   You can also provide credentials when prompted by the application.

## Usage

### Quick Start - Run Once

**Run the popup review dialog**:
```bash
uv run python popup_review.py
```

Enter topics you want to review, and AI-generated questions will be saved.

**Run the quiz**:
```bash
uv run python quiz_review.py
```

Answer questions from your saved topics.

### Automated Scheduling (Windows)

For continuous practice, schedule the system to run every 4 hours:

1. **Read the setup guide**:
   ```
   SCHEDULER_SETUP_GUIDE.md
   ```

2. **Run the scheduler manually** (for testing):
   ```bash
   uv run python schedule_quiz_runner.py
   ```

3. **Set up Windows Task Scheduler** to run automatically at startup:
   - Follow instructions in `SCHEDULER_SETUP_GUIDE.md`
   - Or run: `schedule_quiz_at_startup.ps1` (requires PowerShell admin)

## Project Structure

```
ai_powered_popup_review/
├── popup_review.py              # Popup GUI to collect topics
├── quiz_review.py               # Quiz application
├── schedule_quiz_runner.py      # Main scheduler orchestrator
├── schedule_quiz_at_startup.ps1 # PowerShell script for Task Scheduler setup
├── pyproject.toml               # Project dependencies
├── README.md                    # This file
├── SCHEDULER_SETUP_GUIDE.md     # Detailed scheduler setup instructions
├── quiz_history.json            # Stores quiz execution history
├── quiz_review.json             # Current quiz questions and responses
└── schedule_quiz_runner.log     # Scheduler execution logs
```

## How It Works

### Workflow

1. **Startup**: `schedule_quiz_runner.py` launches at system startup
2. **Topic Collection**: `popup_review.py` opens a dialog to enter topics
3. **Question Generation**: AI generates multiple-choice questions for each topic
4. **Quiz Time**: Every 4 hours, `quiz_review.py` automatically launches
5. **User Practice**: Answer or skip questions; view AI-generated solutions
6. **Data Storage**: All responses are saved to JSON files for review

## Configuration

### Scheduler Settings

Edit `schedule_quiz_runner.py` to adjust:

- `QUIZ_INTERVAL_HOURS`: Interval between quiz runs (default: 4 hours)
- `MAX_QUIZ_EXECUTIONS`: Maximum daily quiz runs (default: 3)
- Log file location and format

## Troubleshooting

### Quiz doesn't start
- Check `schedule_quiz_runner.log` for errors
- Verify OPENAI_API_KEY is set in `.env`
- Ensure all dependencies are installed: `uv sync`

### API errors
- Verify your API key is valid
- Check internet connection
- Confirm API endpoint is correct in `.env`

### Task Scheduler not running
- Verify the PowerShell script ran with admin privileges
- Check Windows Event Viewer for task execution errors
- See `SCHEDULER_SETUP_GUIDE.md` for detailed instructions
