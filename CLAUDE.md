# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Start Development Server
```bash
python run.py
```
This starts the FastAPI server on port 8000 with hot reload enabled.

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Tests
```bash
# Run all test files
python run_all_tests.py

# Run individual test suites
python -m pytest tests/

# Run specific test cases
python test_case_runner.py --prompt "Save my battery"

# Run automated scenario tests
python automated_test.py

# Performance benchmarking
python benchmark.py --prompt battery --requests 20
```

### Database Operations
```bash
# Reset database (use with caution)
python reset_db.py

# Inspect database contents
python inspect_db.py

# Seed test data
python seed_test_data.py
```

## Architecture Overview

PowerGuard is a Python FastAPI-based AI backend service that provides intelligent battery and data optimization recommendations for Android devices.

### Core Components

- **FastAPI Server** (`app/main.py`): REST API with endpoints for device analysis
- **LLM Service** (`app/llm_service.py`): Integration with Groq API for AI-powered analysis
- **Prompt Analyzer** (`app/prompt_analyzer.py`): Intelligent parsing of user prompts and intent detection
- **Strategy Analyzer** (`app/utils/strategy_analyzer.py`): Determines optimization strategies based on battery level and constraints
- **Actionable Generator** (`app/utils/actionable_generator.py`): Creates specific optimization actions
- **Insight Generator** (`app/utils/insight_generator.py`): Generates explanatory insights for users
- **Database Layer** (`app/database.py`): SQLAlchemy ORM with SQLite for usage pattern storage

### Key Features

1. **Smart Prompt Analysis**: Distinguishes between information requests ("What apps use most battery?") and optimization requests ("Save my battery")
2. **Battery-Level Strategy**: Adapts aggressiveness based on current battery level (≤10% = very aggressive, >50% = minimal)
3. **Critical App Protection**: Recognizes and protects essential apps (messaging, navigation, email, work apps) during optimization
4. **Time Constraint Processing**: Handles user requests like "need battery to last 3 hours"
5. **Data Constraint Handling**: Processes limitations like "only have 500MB data left"
6. **Rate Limiting**: Built-in protection against API abuse

### API Endpoints

- `POST /api/analyze`: Main analysis endpoint accepting device data and optional user prompt
- `GET /api/patterns/{device_id}`: Retrieve usage patterns for specific device
- `POST /api/reset-db`: Reset database (caution required)
- `GET /api/all-entries`: Get all database entries
- `GET /api/test/with-prompt/{prompt}`: Test endpoint with prompt
- `GET /api/test/no-prompt`: Test endpoint without prompt

### Environment Variables

Required environment variable:
- `GROQ_API_KEY`: API key for Groq LLM service

Create a `.env` file in the root directory with this variable.

## Code Patterns and Conventions

### Request/Response Flow
1. Device data + optional prompt received via `/api/analyze`
2. Rate limiting and validation applied
3. Prompt analyzed for intent and constraints
4. Strategy determined based on battery level and constraints
5. Actionables and insights generated via LLM
6. Usage patterns stored in database
7. Comprehensive response returned

### App Category Recognition
The system recognizes these critical app categories:
- **Messaging**: WhatsApp, Messenger, Telegram, Signal, WeChat
- **Navigation**: Google Maps, Waze, Apple Maps, Mapbox, HERE Maps
- **Email**: Gmail, Outlook, ProtonMail, Apple Mail
- **Work/Productivity**: Slack, Teams, Zoom, Office apps
- **Health & Safety**: Health monitoring, Emergency services

### Strategy Aggressiveness Levels
- **≤10% battery**: Very Aggressive (maximum restrictions)
- **≤30% battery**: Aggressive (strong background restrictions)
- **≤50% battery**: Balanced (focus on problematic apps)
- **>50% battery**: Minimal (light optimizations only)

## Testing Strategy

The codebase includes comprehensive testing tools:
- Unit tests in `tests/` directory
- Integration tests via `automated_test.py`
- Performance benchmarking via `benchmark.py`
- Individual scenario testing via test files with JSON payloads

Always run tests before making changes to ensure functionality remains intact.

## Database Schema

SQLite database with single table:
```sql
CREATE TABLE usage_patterns (
    id INTEGER PRIMARY KEY,
    deviceId TEXT NOT NULL,
    packageName TEXT NOT NULL,
    pattern TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    UNIQUE(deviceId, packageName)
);
```

## Important Implementation Notes

- The system uses a hybrid approach: rule-based pre-classification combined with LLM-powered deep analysis
- Retry mechanisms are built into LLM API calls with exponential backoff
- All responses include battery/data/performance scores and estimated savings
- Critical apps mentioned in prompts are automatically protected during optimization
- Time and data constraints from user prompts directly influence strategy aggressiveness