"""
Comprehensive Error Handling and Logging Utilities
Provides standardized error responses and logging formats
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standard error codes for API responses"""
    # Client Errors (4xx)
    INVALID_INPUT = "invalid_input"
    MISSING_REQUIRED = "missing_required_field"
    INVALID_LOCATION = "invalid_location"
    INVALID_COORDINATES = "invalid_coordinates"
    
    # Server Errors (5xx)
    INTERNAL_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    API_FAILED = "external_api_failed"
    ML_MODEL_ERROR = "ml_model_error"
    DATABASE_ERROR = "database_error"
    CACHE_ERROR = "cache_error"
    
    # Custom Errors
    NO_RESULTS = "no_results_found"
    TIMEOUT = "request_timeout"


class APIError(Exception):
    """Standard API error"""
    
    def __init__(self, code: ErrorCode, message: str, status_code: int = 500,
                 details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to response dictionary"""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "status": self.status_code,
                "details": self.details,
                "timestamp": self.timestamp
            }
        }
    
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


class ValidationError(APIError):
    """Validation error - 400"""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(
            code=ErrorCode.INVALID_INPUT,
            message=message,
            status_code=400,
            details=details
        )


class NotFoundError(APIError):
    """Not found error - 404"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code=ErrorCode.NO_RESULTS,
            message=f"{resource} not found: {identifier}",
            status_code=404,
            details={"resource": resource, "identifier": identifier}
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error - 503"""
    def __init__(self, service: str, reason: Optional[str] = None):
        super().__init__(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=f"{service} is unavailable",
            status_code=503,
            details={"service": service, "reason": reason}
        )


class ExternalAPIError(APIError):
    """External API failure - 502"""
    def __init__(self, provider: str, reason: str):
        super().__init__(
            code=ErrorCode.API_FAILED,
            message=f"Failed to get data from {provider}",
            status_code=502,
            details={"provider": provider, "reason": reason}
        )


def handle_exceptions(default_return=None):
    """
    Decorator to handle exceptions and convert to APIError
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except APIError:
                raise  # Re-raise API errors
            except ValueError as e:
                logger.warning(f"Validation error in {func.__name__}: {str(e)}")
                raise ValidationError(str(e))
            except TimeoutError as e:
                logger.error(f"Timeout in {func.__name__}: {str(e)}")
                raise APIError(
                    code=ErrorCode.TIMEOUT,
                    message=f"Request timeout: {str(e)}",
                    status_code=504
                )
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}\n{traceback.format_exc()}")
                raise APIError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="An unexpected error occurred",
                    status_code=500,
                    details={"function": func.__name__}
                )
        return wrapper
    return decorator


class ErrorLogger:
    """Advanced error logging with context"""
    
    @staticmethod
    def log_error(error: Exception, context: Dict[str, Any] = None, level: str = "error"):
        """
        Log error with additional context
        
        Args:
            error: Exception to log
            context: Additional context information
            level: Logging level (debug, info, warning, error, critical)
        """
        log_func = getattr(logger, level, logger.error)
        
        error_msg = f"[{error.__class__.__name__}] {str(error)}"
        
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            error_msg = f"{error_msg} | Context: {context_str}"
        
        log_func(error_msg)
        
        if level == "error" or level == "critical":
            logger.debug(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def log_request(endpoint: str, method: str, params: Dict[str, Any] = None):
        """Log incoming request"""
        params_str = " | ".join(f"{k}={v}" for k, v in (params or {}).items())
        logger.info(f"📨 {method.upper()} {endpoint} {params_str}")
    
    @staticmethod
    def log_response(endpoint: str, status_code: int, duration_ms: float = None):
        """Log outgoing response"""
        status_str = "✓" if 200 <= status_code < 300 else "⚠️" if 400 <= status_code < 500 else "❌"
        duration_str = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        logger.info(f"{status_str} Response: {status_code}{duration_str}")
    
    @staticmethod
    def log_performance_warning(operation: str, duration_ms: float, threshold_ms: float = 1000):
        """Log warning if operation exceeds threshold"""
        if duration_ms > threshold_ms:
            logger.warning(f"⚠️ Slow operation: {operation} took {duration_ms:.0f}ms (threshold: {threshold_ms}ms)")


class HealthCheck:
    """Health check utilities"""
    
    def __init__(self):
        self.status = {
            "database": False,
            "cache": False,
            "ml_model": False,
            "api_services": {}
        }
        self.checks_completed = False
    
    def check_database(self, db) -> bool:
        """Check database connectivity"""
        try:
            # Simple query to verify connectivity
            db.get_all_locations()
            self.status["database"] = True
            logger.info("✓ Database health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            self.status["database"] = False
            return False
    
    def check_cache(self, cache) -> bool:
        """Check cache connectivity"""
        try:
            cache.ping()
            self.status["cache"] = True
            logger.info("✓ Cache health check passed")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Cache health check failed: {e} (system will work without cache)")
            self.status["cache"] = False
            return False
    
    def check_ml_model(self, model) -> bool:
        """Check ML model"""
        try:
            if model and model.is_ready():
                self.status["ml_model"] = True
                logger.info("✓ ML model health check passed")
                return True
            else:
                self.status["ml_model"] = False
                logger.warning("⚠️ ML model not ready")
                return False
        except Exception as e:
            logger.error(f"❌ ML model health check failed: {e}")
            self.status["ml_model"] = False
            return False
    
    def check_api_services(self, api_service) -> Dict[str, bool]:
        """Check external API services"""
        try:
            status = api_service.get_status()
            self.status["api_services"] = status
            logger.info("✓ API services health check passed")
            return status
        except Exception as e:
            logger.warning(f"⚠️ API services health check failed: {e}")
            return {}
    
    def run_all_checks(self, dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """Run all health checks"""
        logger.info("🏥 Starting health checks...")
        
        if "database" in dependencies:
            self.check_database(dependencies["database"])
        
        if "cache" in dependencies:
            self.check_cache(dependencies["cache"])
        
        if "ml_model" in dependencies:
            self.check_ml_model(dependencies["ml_model"])
        
        if "api_service" in dependencies:
            self.check_api_services(dependencies["api_service"])
        
        self.checks_completed = True
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": self.status,
            "overall_health": self._calculate_overall_health()
        }
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        critical = self.status.get("database", False) and self.status.get("ml_model", False)
        
        if critical:
            return "HEALTHY"
        else:
            return "DEGRADED"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": self.status,
            "overall": self._calculate_overall_health()
        }


def create_success_response(data: Any, message: str = None, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        "success": True,
        "data": data,
        "message": message or "Success",
        "meta": meta or {},
        "timestamp": datetime.utcnow().isoformat()
    }


def create_error_response(error: APIError) -> Tuple[Dict[str, Any], int]:
    """Create standardized error response"""
    return error.to_dict(), error.status_code
