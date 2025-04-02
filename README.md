# PowerGuard Backend

A FastAPI-based backend service for PowerGuard, integrating with Groq LLM for intelligent power management.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure

- `app/`: Main application package
  - `main.py`: FastAPI application entry point
  - `models.py`: Pydantic models for request/response
  - `llm_service.py`: Groq LLM integration
  - `database.py`: SQLite database setup
  - `schemas/`: JSON schemas for data validation

- `tests/`: Test suite
  - `test_api.py`: API endpoint tests

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 