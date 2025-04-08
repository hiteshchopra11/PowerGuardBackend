# PowerGuard AI Backend Architecture

## High-Level Design (HLD)

### System Architecture

```mermaid
graph TD
    A[Android App] -->|Device Data| B[PowerGuard Backend]
    B -->|Analysis Request| C[Groq LLM Service]
    B -->|Store/Retrieve| D[(SQLite DB)]
    
    subgraph "PowerGuard Backend"
        B1[FastAPI Server]
        B2[Data Processor]
        B3[Pattern Analyzer]
        B4[Rate Limiter]
        B5[Prompt Analyzer]
        B6[Strategy Determiner]
        B7[Actionable Generator]
        B8[Insight Generator]
        B9[Error Handler]
        
        B1 --> B2
        B1 --> B4
        B2 --> B3
        B2 --> B5
        B5 --> B6
        B6 --> B7
        B6 --> B8
        B1 --> B9
    end
    
    subgraph "Groq LLM Service"
        C1[LLM Model]
        C2[Pattern Recognition]
        C3[Recommendation Engine]
        C4[Constraint Analysis]
        C5[Prompt Classification]
        
        C1 --> C2
        C1 --> C5
        C2 --> C3
        C5 --> C4
        C4 --> C3
    end
```

### Layered Architecture

```mermaid
graph TD
    subgraph "User Interface Layer"
        A[Android App]
    end
    
    subgraph "API Gateway Layer"
        B1[FastAPI Server]
        B4[Rate Limiter]
        B9[Error Handler]
    end
    
    subgraph "Processing Layer"
        B2[Data Processor]
        B3[Pattern Analyzer]
        B5[Prompt Analyzer]
        B6[Strategy Determiner]
    end
    
    subgraph "Generation Layer"
        B7[Actionable Generator]
        B8[Insight Generator]
    end
    
    subgraph "Intelligence Layer"
        C[Groq LLM Service]
    end
    
    subgraph "Data Layer"
        D[SQLite Database]
    end
    
    A -->|Device Data| B1
    B1 --> B2
    B1 --> B4
    B1 --> B9
    B2 --> B3
    B2 --> B5
    B5 --> B6
    B6 --> B7
    B6 --> B8
    B3 --> C
    B5 --> C
    B7 --> C
    B3 --> D
    D --> B3
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
   - Rate limiting and DDoS protection
   - Error handling and logging
   - Prompt analysis and classification
   - Strategy determination
   - Actionable generation
   - Insight generation

3. **AI Service**
   - Groq LLM for intelligent analysis
   - Pattern recognition
   - Recommendation generation
   - Retry mechanism for API calls
   - Constraint extraction and analysis
   - Prompt classification

### Data Flow

```mermaid
sequenceDiagram
    participant App as Android App
    participant API as PowerGuard API
    participant RL as Rate Limiter
    participant DP as Data Processor
    participant PA as Prompt Analyzer
    participant SD as Strategy Determiner
    participant AG as Actionable Generator
    participant IG as Insight Generator
    participant DB as SQLite DB
    participant LLM as Groq LLM
    
    App->>API: POST /api/analyze with prompt
    API->>RL: Check Rate Limit
    RL-->>API: Rate Limit OK
    Note over API: Validate Request
    API->>DP: Process Device Data
    DP->>PA: Analyze User Prompt
    PA->>LLM: Send prompt for classification
    LLM-->>PA: Return prompt classification
    PA->>SD: Determine Strategy
    SD->>DB: Get Historical Patterns
    DB-->>SD: Return Patterns
    SD->>AG: Generate Actionables
    SD->>IG: Generate Insights
    AG->>LLM: Send Actionable Generation Request
    LLM-->>AG: Return Generated Actionables
    IG->>LLM: Send Insight Generation Request
    LLM-->>IG: Return Generated Insights
    AG-->>API: Return Actionables
    IG-->>API: Return Insights
    API->>DB: Store New Patterns
    DB-->>API: Confirm Storage
    API-->>App: Return Complete Response
```

### Smart Prompt Analysis Flow

```mermaid
graph TD
    A[User Prompt] --> B[Information or Optimization Request?]
    B -->|Information| C[Extract Resource Type]
    B -->|Optimization| D[Extract Constraints]
    C --> C1[Battery Information?]
    C --> C2[Data Information?]
    C --> C3[Performance Information?]
    D --> F[Identify Critical Apps]
    D --> G[Extract Time Constraints]
    D --> H[Extract Data Constraints]
    
    F --> F1[Match App Categories]
    F --> F2[Map to Actual Apps]
    
    G --> G1[Parse Duration]
    G --> G2[Calculate End Time]
    
    H --> H1[Parse Data Amount]
    H --> H2[Calculate Usage Rate]
    
    F1 --> I[Strategy Generation]
    F2 --> I
    G1 --> I
    G2 --> I
    H1 --> I
    H2 --> I
    C1 --> E1[Generate Battery Information Insights]
    C2 --> E2[Generate Data Information Insights]
    C3 --> E3[Generate Performance Information Insights]
    
    I --> J[Battery Level Analysis]
    J --> K[Determine Aggressiveness]
    
    K -->|Critical Battery| L1[Very Aggressive Strategy]
    K -->|Low Battery| L2[Aggressive Strategy]
    K -->|Moderate Battery| L3[Balanced Strategy]
    K -->|High Battery| L4[Minimal Strategy]
    
    L1 --> L[Generate Actionables]
    L2 --> L
    L3 --> L
    L4 --> L
    
    K --> M[Generate Optimization Insights]
    
    L --> N[Final Response]
    M --> N
    E1 --> N
    E2 --> N
    E3 --> N
```

## API Documentation

### Endpoints

#### POST /api/analyze
Analyzes device data and returns optimization recommendations.

**Request Body:**
```json
{
    "deviceId": "string",
    "timestamp": "integer",
    "battery": {
        "level": "float",
        "health": "float",
        "temperature": "float"
    },
    "memory": {
        "total": "integer",
        "used": "integer",
        "free": "integer"
    },
    "cpu": {
        "usage": "float",
        "temperature": "float"
    },
    "network": {
        "dataUsed": "float",
        "wifiEnabled": "boolean",
        "mobileDataEnabled": "boolean"
    },
    "apps": [
        {
            "packageName": "string",
            "batteryUsage": "float",
            "dataUsage": "float",
            "foregroundTime": "integer"
        }
    ],
    "prompt": "string"  // Optional
}
```

**Response:**
```json
{
    "id": "string",
    "success": "boolean",
    "timestamp": "float",
    "message": "string",
    "actionable": [
        {
            "id": "string",
            "type": "string",
            "packageName": "string",
            "description": "string",
            "reason": "string",
            "newMode": "string",
            "parameters": {}
        }
    ],
    "insights": [
        {
            "type": "string",
            "title": "string",
            "description": "string",
            "severity": "string"
        }
    ],
    "batteryScore": "float",
    "dataScore": "float",
    "performanceScore": "float",
    "estimatedSavings": {
        "batteryMinutes": "float",
        "dataMB": "float"
    }
}
```

#### GET /api/patterns/{device_id}
Retrieves stored usage patterns for a specific device.

**Response:**
```json
{
    "packageName1": "pattern1",
    "packageName2": "pattern2"
}
```

#### POST /api/reset-db
Resets the database (use with caution).

**Response:**
```json
{
    "status": "success",
    "message": "Database reset successfully completed"
}
```

#### GET /api/all-entries
Retrieves all database entries.

**Response:**
```json
[
    {
        "id": "integer",
        "device_id": "string",
        "package_name": "string",
        "pattern": "string",
        "timestamp": "string",
        "raw_timestamp": "integer"
    }
]
```

### Rate Limits

- Default endpoints: 1000 requests per minute
- Analyze endpoint: 500 requests per minute
- Patterns endpoint: 1000 requests per minute
- Reset DB endpoint: 100 requests per hour

### Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 429: Too Many Requests
- 500: Internal Server Error

Error responses include:
```json
{
    "error": "string",
    "message": "string",
    "timestamp": "integer",
    "path": "string"
}
```

## Low-Level Design (LLD)

### Database Schema

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
   - Prompt analysis and classification
   - User-directed optimization focus
   - Critical app protection
   - Battery level based strategies
   - Time and data constraint handling
   - Information vs optimization request detection

3. **Storage Layer**
   - SQLite database
   - Pattern persistence
   - Historical data storage

4. **Security Layer**
   - Rate limiting
   - Input validation
   - Error handling
   - Logging

### Smart Prompt Analysis

The system implements an intelligent prompt analysis pipeline that understands user intentions:

#### Information Request Handling

When a user asks for information (e.g., "What apps are using the most battery?"), the system:

1. Identifies the request as an information request
2. Determines the resource type of interest (battery, data, or both)
3. Retrieves the relevant resource usage data
4. Generates insights with the requested information
5. Returns a response with insights but no actionable recommendations

```mermaid
sequenceDiagram
    participant User
    participant API
    participant PA as Prompt Analyzer
    participant LLM
    participant IR as Information Response Generator
    
    User->>API: "What apps are using the most battery?"
    API->>PA: Analyze Prompt
    PA->>LLM: Classify Prompt
    LLM-->>PA: Information Request (Battery)
    PA->>IR: Generate Information Response
    IR->>LLM: Request Battery Usage Insights
    LLM-->>IR: Battery Usage Insights
    IR-->>API: Response with Insights, No Actionables
    API-->>User: Information Response
```

#### Optimization Request Handling

When a user asks for optimization (e.g., "Save my battery" or "I need maps for 3 hours"), the system:

1. Identifies the request as an optimization request
2. Identifies any critical app categories mentioned (e.g., messaging, navigation)
3. Extracts time constraints if mentioned (e.g., "for 3 hours")
4. Extracts data constraints if mentioned (e.g., "500MB left")
5. Analyzes battery level to determine base strategy aggressiveness
6. Adjusts strategy based on time and data constraints
7. Generates actionables that protect critical apps and optimize others
8. Generates insights explaining the strategy and expected savings
9. Returns a comprehensive response with actionables and insights

```mermaid
sequenceDiagram
    participant User
    participant API
    participant PA as Prompt Analyzer
    participant LLM
    participant SD as Strategy Determiner
    participant AG as Actionable Generator
    participant IG as Insight Generator
    
    User->>API: "Save battery, need messaging apps"
    API->>PA: Analyze Prompt
    PA->>LLM: Classify Prompt
    LLM-->>PA: Optimization Request (Battery)
    PA->>LLM: Extract Critical Apps
    LLM-->>PA: Critical Apps (Messaging)
    PA->>SD: Determine Strategy
    SD->>LLM: Request Strategy Based on Constraints
    LLM-->>SD: Strategy (e.g., Aggressive)
    SD->>AG: Generate Actionables
    SD->>IG: Generate Insights
    AG->>LLM: Request Actionables with App Protection
    LLM-->>AG: Actionables with Messaging Apps Protected
    IG->>LLM: Request Strategy Insights
    LLM-->>IG: Strategy Insights
    AG-->>API: Actionables
    IG-->>API: Insights
    API-->>User: Optimization Response
```

### Critical App Categories

The system recognizes specific app categories that users often need to keep working:

1. **Messaging Apps**
   - WhatsApp, Messenger, Telegram, Signal, WeChat
   - Keywords: "messaging", "chat", "communication", "WhatsApp", "Messenger"

2. **Navigation Apps**
   - Google Maps, Waze, Mapbox, Apple Maps, HERE Maps
   - Keywords: "maps", "navigation", "directions", "GPS", "Google Maps"

3. **Email Apps**
   - Gmail, Outlook, ProtonMail, Apple Mail
   - Keywords: "email", "mail", "Gmail", "Outlook"

4. **Work/Productivity Apps**
   - Slack, Microsoft Teams, Zoom, Office apps
   - Keywords: "work", "office", "productivity", "Slack", "Teams", "Zoom"

5. **Health & Safety Apps**
   - Health monitoring, Emergency services
   - Keywords: "health", "emergency", "medical", "safety"

When users mention these categories (e.g., "need messages" or "using maps"), the system ensures these apps remain fully functional while optimizing other resources.

### Battery Level Based Strategies

The system adapts its optimization strategy based on current battery level:

| Battery Level | Strategy | Approach | App Treatment | UI Adjustments |
|--------------|----------|----------|--------------|----------------|
| ≤10% | Very Aggressive | Maximum restrictions on non-critical apps | Kill background for all non-critical, restrict even moderately used apps | Reduce brightness significantly, force dark mode, disable animations |
| ≤30% | Aggressive | Strong restrictions on background activity | Restrict background for most apps, optimize moderately used apps | Reduce brightness moderately, suggest dark mode, reduce animations |
| ≤50% | Moderate | Balanced approach focusing on problematic apps | Restrict only high-consuming apps, optimize moderate consumers | Suggest brightness reduction, normal animations |
| >50% | Minimal | Light optimizations only for the most resource-intensive apps | Restrict only extremely high consumers | No UI adjustments |

This adaptive approach ensures that battery-saving measures are proportional to the urgency of the situation.

### Time Constraint Processing

When users specify a time constraint (e.g., "need battery to last 3 hours"), the system:

1. Extracts the duration (3 hours)
2. Calculates target end time (current time + 3 hours)
3. Estimates current battery drain rate based on usage patterns
4. Determines if normal drain rate will satisfy the time constraint
5. If not, adjusts strategy aggressiveness to meet the time requirement
6. Prioritizes critical apps mentioned in the prompt
7. Applies more aggressive restrictions to non-critical apps when necessary

```mermaid
graph TD
    A[Extract Time Constraint] --> B[Calculate End Time]
    B --> C[Estimate Battery Drain Rate]
    C --> D{Will Battery Last?}
    D -->|Yes| E[Apply Normal Strategy]
    D -->|No| F[Increase Strategy Aggressiveness]
    F --> G[Calculate Required Savings]
    G --> H[Apply Targeted Restrictions]
    H --> I[Protect Critical Apps]
    I --> J[Generate Time-Based Insights]
```

### Data Constraint Processing

When users specify a data constraint (e.g., "only have 500MB left"), the system:

1. Extracts the data limit (500MB)
2. Estimates current data usage rate based on app patterns
3. Identifies high data-consuming apps
4. Applies appropriate restrictions based on app importance
5. Generates data-saving recommendations
6. Provides estimated data savings

```mermaid
graph TD
    A[Extract Data Constraint] --> B[Estimate Usage Rate]
    B --> C[Identify Data-Hungry Apps]
    C --> D[Classify App Importance]
    D --> E[Apply Data Restrictions]
    E --> F[Generate Data-Saving Insights]
    F --> G[Calculate Estimated Savings]
```

### Implementation Details

1. **FastAPI Application**
   - Uses dependency injection for database sessions
   - Implements middleware for rate limiting
   - Provides comprehensive error handling
   - Includes detailed logging

2. **LLM Integration**
   - Uses Groq API with retry mechanism
   - Implements exponential backoff
   - Handles API failures gracefully
   - Provides fallback responses

3. **Database Operations**
   - Uses SQLAlchemy ORM
   - Implements connection pooling
   - Provides session management
   - Includes error handling

4. **Rate Limiting**
   - Implements token bucket algorithm
   - Provides configurable limits per endpoint
   - Includes detailed logging
   - Handles edge cases gracefully

5. **Prompt Analysis Pipeline**
   - Rule-based pre-classification
   - LLM-based deep analysis
   - Constraint extraction
   - Category recognition
   - Intent determination

6. **Strategy Determination**
   - Battery level thresholds
   - Constraint-based adjustments
   - Critical app protection
   - Resource usage analysis
   - Time-based planning

7. **Response Generation**
   - Actionable generation based on strategy
   - Insight generation based on request type
   - Resource score calculation
   - Savings estimation
   - Response assembly 