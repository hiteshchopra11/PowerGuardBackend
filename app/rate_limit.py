from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_rate_limit')

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Configure rate limits - DISABLED for testing by setting extremely high limits
# Format: "number of requests per time period"
RATE_LIMITS = {
    "default": "1000000/second",  # Effectively disabled
    "analyze": "1000000/second",   # Effectively disabled
    "patterns": "1000000/second",  # Effectively disabled
    "reset_db": "1000000/second"   # Effectively disabled
}

def setup_rate_limiting(app):
    """Configure rate limiting for the application"""
    try:
        # Add rate limiter to app
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        # Log that rate limiting is disabled
        logger.warning("RATE LIMITING IS DISABLED FOR TESTING!")
        
        # Add rate limit decorators to routes
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            try:
                # Just pass through all requests without actual rate limiting
                response = await call_next(request)
                return response
                
            except Exception as e:
                logger.error(f"Error in rate limit middleware: {str(e)}")
                return await call_next(request)
                
    except Exception as e:
        logger.error(f"Error setting up rate limiting: {str(e)}")
        raise 