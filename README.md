# PowerGuard AI Backend

A battery optimization service that uses AI to analyze device usage patterns and provide actionable recommendations for better battery life.

## Features

- Device usage analysis
- Battery optimization recommendations
- Usage pattern tracking
- Historical data analysis
- AI-powered insights
- Rate limiting and DDoS protection

## API Endpoints

- `POST /api/analyze` - Analyze device data and get optimization recommendations
- `GET /api/patterns/{device_id}` - Get usage patterns for a specific device
- `POST /api/reset-db` - Reset the database (use with caution)
- `GET /api/all-entries` - Get all database entries

## Rate Limits

To prevent abuse and ensure fair usage, the following rate limits are in place:

- Default endpoints: 100 requests per minute
- Analyze endpoint: 30 requests per minute
- Patterns endpoint: 60 requests per minute
- Reset DB endpoint: 5 requests per hour

When rate limits are exceeded, the API will return a 429 (Too Many Requests) status code.

## High-Level Design (HLD)

### System Architecture

```mermaid
graph LR
    A[Android App] <-->|Device Data| B[PowerGuard Backend]
    B <-->|Analysis Request| C[Groq LLM Service]
    B <-->|Store/Retrieve| D[(SQLite DB)]
    
    subgraph "PowerGuard Backend"
        B1[FastAPI Server]
        B2[Data Processor]
        B3[Pattern Analyzer]
        B1 --> B2
        B2 --> B3
    end
    
    subgraph "Groq LLM Service"
        C1[LLM Model]
        C2[Pattern Recognition]
        C3[Recommendation Engine]
        C1 --> C2
        C2 --> C3
    end
```

### Components
1. **Client Application**
   - Android app collecting device data
   - Sends usage statistics to backend
   - Receives and displays recommendations

2. **Backend Service**
   - FastAPI-based REST API
   - SQLite database for data persistence
   - Integration with Groq LLM
   - Usage pattern analysis

3. **AI Service**
   - Groq LLM for intelligent analysis
   - Pattern recognition
   - Recommendation generation

### Data Flow

```mermaid
sequenceDiagram
    participant App as Android App
    participant API as PowerGuard API
    participant DB as SQLite DB
    participant LLM as Groq LLM
    
    App->>API: POST /api/analyze
    Note over API: Validate Request
    API->>DB: Get Historical Patterns
    DB-->>API: Return Patterns
    API->>LLM: Send Analysis Request
    LLM-->>API: Generate Recommendations
    API->>DB: Store New Patterns
    DB-->>API: Confirm Storage
    API-->>App: Return Recommendations
    
    Note over App,API: Periodic Updates
    App->>API: GET /api/patterns/{device_id}
    API->>DB: Query Patterns
    DB-->>API: Return Patterns
    API-->>App: Return Updated Patterns
```

## Low-Level Design (LLD)

### Database Schema
```sql
CREATE TABLE usage_patterns (
    id INTEGER PRIMARY KEY,
    device_id TEXT NOT NULL,
    package_name TEXT NOT NULL,
    pattern TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    UNIQUE(device_id, package_name)
);
```

### API Models
1. **DeviceData**
   - App usage information
   - Battery statistics
   - Network usage data
   - Wake lock information

2. **ActionResponse**
   - List of actionable recommendations
   - Summary of changes
   - Usage patterns
   - Timestamp

### Key Components
1. **Data Collection**
   - App usage tracking
   - Battery monitoring
   - Network usage tracking
   - Wake lock detection

2. **Analysis Engine**
   - Pattern recognition
   - Historical data analysis
   - Recommendation generation

3. **Storage Layer**
   - SQLite database
   - Pattern persistence
   - Historical data storage

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```
   GROQ_API_KEY=your_api_key_here
   ```
5. Run the application:
   ```bash
   python run.py
   ```

## API Documentation

Access the interactive API documentation at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Development

- Python 3.9+
- FastAPI
- SQLAlchemy
- Groq LLM API
- SQLite

## License

MIT License 