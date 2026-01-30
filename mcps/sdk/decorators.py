"""
Decorators for MCP development
"""

import functools
import time
import logging
from typing import Callable, Any, Optional, List

logger = logging.getLogger(__name__)


def mcp_endpoint(
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """
    Mark a method as an MCP endpoint

    Usage:
        @mcp_endpoint(name="process_invoice", description="Process invoice from PDF")
        async def process_invoice(self, file_path: str, ctx: MCPContext):
            ...
    """
    def decorator(func: Callable) -> Callable:
        endpoint_name = name or func.__name__
        endpoint_desc = description or func.__doc__ or ""
        endpoint_tags = tags or []

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # Store metadata
        wrapper._is_mcp_endpoint = True
        wrapper._endpoint_name = endpoint_name
        wrapper._endpoint_description = endpoint_desc
        wrapper._endpoint_tags = endpoint_tags

        return wrapper

    return decorator


def requires_model(model_name: str):
    """
    Ensure a model is loaded before executing function

    Usage:
        @requires_model("invoice-ocr")
        async def ocr_document(self, file_path: str, ctx: MCPContext):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Extract context from args/kwargs
            ctx = None
            for arg in args:
                if hasattr(arg, "model_server"):
                    ctx = arg
                    break
            if not ctx:
                ctx = kwargs.get("ctx")

            if not ctx:
                raise ValueError("MCPContext not found in function arguments")

            # Ensure model is loaded
            await self.ensure_model_loaded(model_name, ctx)

            # Call original function
            return await func(self, *args, **kwargs)

        wrapper._required_model = model_name
        return wrapper

    return decorator


def track_usage(
    billable: bool = True,
    unit: str = "document"
):
    """
    Track usage for billing

    Usage:
        @track_usage(billable=True, unit="document")
        async def process_document(self, data: dict, ctx: MCPContext):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            start_time = time.time()

            try:
                # Execute function
                result = await func(self, *args, **kwargs)

                # Track successful usage
                processing_time = int((time.time() - start_time) * 1000)

                if billable:
                    # Extract context
                    ctx = None
                    for arg in args:
                        if hasattr(arg, "engagement_id"):
                            ctx = arg
                            break
                    if not ctx:
                        ctx = kwargs.get("ctx")

                    if ctx:
                        self._track_usage(
                            model="function",
                            input_tokens=0,
                            output_tokens=0,
                            processing_time_ms=processing_time,
                            ctx=ctx
                        )

                return result

            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise

        wrapper._is_tracked = True
        wrapper._billable = billable
        wrapper._billing_unit = unit
        return wrapper

    return decorator


def cache_result(ttl_seconds: int = 3600):
    """
    Cache function results

    Usage:
        @cache_result(ttl_seconds=1800)
        async def expensive_operation(self, input_data: dict):
            ...
    """
    cache = {}

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = str((args, tuple(sorted(kwargs.items()))))

            # Check cache
            if cache_key in cache:
                cached_data, cached_time = cache[cache_key]
                if time.time() - cached_time < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_data

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            cache[cache_key] = (result, time.time())

            return result

        wrapper._is_cached = True
        wrapper._cache_ttl = ttl_seconds
        return wrapper

    return decorator


def retry_on_failure(max_retries: int = 3, delay_seconds: float = 1.0):
    """
    Retry function on failure

    Usage:
        @retry_on_failure(max_retries=3, delay_seconds=2.0)
        async def flaky_operation(self, data: dict):
            ...
    """
    import asyncio

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}"
                    )

                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay_seconds * (attempt + 1))

            # All retries failed
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        wrapper._max_retries = max_retries
        wrapper._retry_delay = delay_seconds
        return wrapper

    return decorator


def validate_input(schema: dict):
    """
    Validate input data against schema

    Usage:
        @validate_input({"file_path": str, "language": str})
        async def process_file(self, file_path: str, language: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Basic type checking
            func_signature = func.__annotations__

            for param_name, param_type in schema.items():
                # Check in kwargs
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not isinstance(value, param_type):
                        raise TypeError(
                            f"Parameter '{param_name}' must be {param_type}, "
                            f"got {type(value)}"
                        )

            return await func(*args, **kwargs)

        wrapper._input_schema = schema
        return wrapper

    return decorator


def async_timeout(seconds: float):
    """
    Add timeout to async function

    Usage:
        @async_timeout(30.0)
        async def long_running_task(self, data: dict):
            ...
    """
    import asyncio

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} timed out after {seconds}s")
                raise TimeoutError(
                    f"Function {func.__name__} exceeded timeout of {seconds}s"
                )

        wrapper._timeout_seconds = seconds
        return wrapper

    return decorator
