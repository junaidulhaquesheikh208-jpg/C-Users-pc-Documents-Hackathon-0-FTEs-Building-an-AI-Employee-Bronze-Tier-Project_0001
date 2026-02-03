import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple


logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Exception for transient errors that might resolve on retry"""
    pass


def with_retry(
    max_attempts: int = 3, 
    base_delay: float = 1, 
    max_delay: float = 60,
    backoff_factor: float = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to add retry logic to functions
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor by which delay increases after each retry
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt, raise the exception
                        logger.error(f"All {max_attempts} attempts failed. Last error: {e}")
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
            
            # This shouldn't be reached, but added for type checker
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Example of how to use the retry decorator
    @with_retry(max_attempts=3, base_delay=1, exceptions=(ConnectionError, TimeoutError))
    def unstable_network_call():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise ConnectionError("Network error occurred")
        return "Success!"
    
    try:
        result = unstable_network_call()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Final failure: {e}")