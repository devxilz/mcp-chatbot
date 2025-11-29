from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.core.settings import get_settings

# ============================================================
# Load global application settings (name, version, debug, etc.)
# ============================================================
settings = get_settings()


# ============================================================
# APPLICATION FACTORY
#
# Purpose of create_app():
# - Clean separation between configuration and execution
# - Helps in scaling large applications
# - Makes testing easier (each test can create a fresh app)
#
# This function returns a fully configured FastAPI instance.
# ============================================================
def create_app() -> FastAPI:
    # --------------------------------------------------------
    # Create FastAPI application with metadata from settings
    #
    # title: Visible in Swagger UI
    # version: Helps in API version tracking
    # debug: Enables more verbose error logs during development
    # --------------------------------------------------------
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    # --------------------------------------------------------
    # ADD CORS MIDDLEWARE
    #
    # CORS (Cross-Origin Resource Sharing) allows the frontend
    # (which may run on a different domain/port) to communicate
    # with this backend API.
    #
    # allow_origins=["*"] allows all domains.
    #     For production, it is better to whitelist specific domains.
    #
    # allow_credentials=True enables cookies/authorization headers.
    #
    # allow_methods and allow_headers control which HTTP methods
    # and headers are allowed by the server.
    # --------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],       # Accept API requests from anywhere (dev mode)
        allow_credentials=True,    # Allow cookies or auth headers
        allow_methods=["*"],       # Allow all HTTP methods (GET/POST/PUT/DELETE/etc.)
        allow_headers=["*"],       # Accept all custom request headers
    )

    # Return the fully configured FastAPI app instance
    return app
