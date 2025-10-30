from functools import wraps
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from helpers.logger import get_logger
from middlewares.auth_middleware import current_user_id
from routes.exceptions import *

logger = get_logger("api_router")

def handle_exceptions(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        user = current_user_id.get()
        try:
            logger.info(f"Attempting {fn.__name__} [user={user}]")
            result = await fn(*args, **kwargs)
            logger.info(f"Success: {fn.__name__} [user={user}]")

            # Standardize response
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result.get("message") if isinstance(result, dict) else None,
                    "data": jsonable_encoder(result.get("data") if isinstance(result, dict) else result)
                }
            )

        # ----- Domain-specific exceptions -----
        except UserAlreadyExists:
            logger.warning(f"UserAlreadyExists: {fn.__name__} [user={user}]")
            return JSONResponse(status_code=400, content={"success": False, "message": "Username already exists", "data": None})

        except UserNotFound:
            logger.warning(f"UserNotFound: {fn.__name__} [user={user}]")
            return JSONResponse(status_code=404, content={"success": False, "message": "User not found", "data": None})

        except InvalidCredentials:
            logger.warning(f"InvalidCredentials: {fn.__name__} [user={user}]")
            return JSONResponse(status_code=401, content={"success": False, "message": "Invalid credentials", "data": None})

        except NotPermitted:
            logger.warning(f"NotPermitted: {fn.__name__} [user={user}]")
            return JSONResponse(status_code=403, content={"success": False, "message": "Not permitted", "data": None})

        except TokenError as e:
            logger.warning(f"TokenError: {fn.__name__} [user={user}] - {str(e)}")
            return JSONResponse(status_code=400, content={"success": False, "message": str(e), "data": None})

        except ProjectNotFound as e:
            logger.warning(f"ProjectNotFound: {fn.__name__} [user={user}] - {str(e)}")
            return JSONResponse(status_code=404, content={"success": False, "message": str(e), "data": None})

        except ProjectExists as e:
            logger.warning(f"ProjectExists: {fn.__name__} [user={user}] - {str(e)}")
            return JSONResponse(status_code=400, content={"success": False, "message": str(e), "data": None})

        except DatabaseError as e:
            logger.error(f"DatabaseError: {fn.__name__} [user={user}] - {str(e)}")
            return JSONResponse(status_code=500, content={"success": False, "message": "Internal server error", "data": None})

        # ----- Common Python errors -----
        except ValueError as e:
            logger.warning(f"ValueError: {fn.__name__} [user={user}] - {str(e)}")
            return JSONResponse(status_code=400, content={"success": False, "message": str(e), "data": None})

        except FileNotFoundError as e:
            logger.warning(f"FileNotFoundError: {fn.__name__} [user={user}] - {str(e)}")
            return JSONResponse(status_code=404, content={"success": False, "message": str(e), "data": None})

        # ----- Catch-all -----
        except Exception as e:
            logger.exception(f"Unhandled error in {fn.__name__} [user={user}] - {str(e)}")
            return JSONResponse(status_code=500, content={"success": False, "message": "Unexpected error", "data": None})

    return wrapper
