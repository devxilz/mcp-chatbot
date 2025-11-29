from app.core.settings import get_settings


def check_health() :
    return {
        "status": "ok",
        "app": get_settings().APP_NAME,
        "version": get_settings().APP_VERSION,
    }
