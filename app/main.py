"""PowerGuard AI Backend - Main FastAPI application."""

import logging
from fastapi import FastAPI

from app.core.database import Base, engine
from app.controllers import analysis_router, patterns_router, health_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_api')

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PowerGuard AI Backend",
    description="""
    PowerGuard AI Backend is an advanced battery and data optimization service that uses AI to analyze device usage patterns
    and provide actionable recommendations for better resource management.
    
    ## Features
    * Advanced AI-powered query processing with 6 category types
    * Battery and data optimization recommendations
    * Smart resource type detection (BATTERY/DATA/OTHER)
    * Information, predictive, optimization, monitoring, and pattern analysis queries
    * Usage pattern tracking and historical analysis
    * Exclusion handling for critical apps
    * User-directed optimizations via natural language prompts
    * Android app-compatible prompt system
    * Hybrid rule-based and LLM prompt classification
    
    ## API Endpoints
    * `/api/analyze` - Analyze device data and get optimization recommendations
    * `/api/patterns/{device_id}` - Get usage patterns for a specific device
    * `/api/reset-db` - Reset the database (use with caution)
    * `/api/all-entries` - Get all database entries
    
    ## Error Handling
    The API uses standard HTTP status codes:
    * 200: Success
    * 400: Bad Request
    * 429: Too Many Requests
    * 500: Internal Server Error
    
    ## Authentication
    Currently, the API does not require authentication.
    
    ## Response Format
    All responses are in JSON format and include:
    * Success/failure status
    * Timestamp
    * Message
    * Data (if applicable)
    """,
    version="1.0.0",
    contact={
        "name": "PowerGuard Team",
        "url": "https://powerguardbackend.onrender.com",
        "email": "support@powerguard.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Analysis",
            "description": "Endpoints for device data analysis and optimization"
        },
        {
            "name": "Patterns",
            "description": "Endpoints for retrieving usage patterns"
        },
        {
            "name": "Database",
            "description": "Endpoints for database management"
        }
    ]
)

# Include routers
app.include_router(analysis_router)
app.include_router(patterns_router)
app.include_router(health_router)