import os

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://superset:superset123@superset-db:5432/superset"
)

FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
}

ENABLE_CORS = True

CORS_OPTIONS = {
    "supports_credentials": True,
    "origins": ["*"],
}

# Allow embedding in iframes from any origin (dev only)
TALISMAN_ENABLED = False
HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}
WTF_CSRF_ENABLED = False

# Guest token for embedded dashboards
GUEST_TOKEN_JWT_SECRET = "wenami-superset-dev-2026"
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_JWT_EXP_SECONDS = 300
GUEST_ROLE_NAME = "Gamma"