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

# Configure rate limits
# Format: "number of requests per time period"
RATE_LIMITS = {
    "default": "1000/minute",  # Default limit for all endpoints
    "analyze": "500/minute",   # Stricter limit for analyze endpoint
    "patterns": "1000/minute", # Moderate limit for patterns endpoint
    "reset_db": "100/hour"     # Very strict limit for database reset
}

def setup_rate_limiting(app):
    """Configure rate limiting for the application"""
    try:
        # Add rate limiter to app
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        # Add rate limit decorators to routes
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            try:
                # Get endpoint path
                path = request.url.path
                
                # Determine rate limit based on endpoint
                if path == "/api/analyze":
                    limit = RATE_LIMITS["analyze"]
                elif path.startswith("/api/patterns/"):
                    limit = RATE_LIMITS["patterns"]
                elif path == "/api/reset-db":
                    limit = RATE_LIMITS["reset_db"]
                else:
                    limit = RATE_LIMITS["default"]
                
                # Create a rate-limited function for this request
                @limiter.limit(limit)
                def rate_limited(request: Request):
                    return None
                
                # Apply rate limit
                rate_limited(request)
                
                # Log rate limit info
                logger.debug(f"Rate limit applied: {limit} for path: {path}")
                
                response = await call_next(request)
                return response
                
            except RateLimitExceeded as e:
                logger.warning(f"Rate limit exceeded for path: {path}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Please try again later.",
                        "timestamp": int(datetime.now().timestamp()),
                        "path": path
                    }
                )
            except Exception as e:
                logger.error(f"Error in rate limit middleware: {str(e)}")
                return await call_next(request)
                
    except Exception as e:
        logger.error(f"Error setting up rate limiting: {str(e)}")
        raise 