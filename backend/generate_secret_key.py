# Generate secure secret key for production
import secrets

print("Generated secure secret key:")
print(secrets.token_urlsafe(32))

# Example .env file content
env_content = """# VedFin Sentinel Environment Configuration
# Generate new SECRET_KEY with: python generate_secret_key.py

# Security
SECRET_KEY=your_generated_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql+asyncpg://sentinel:vedfin_secure_password@localhost:5432/sentinel
REDIS_URL=redis://localhost:6379/0

# ML Models
MODEL_PATH=./ml/artifacts/sentinel_ensemble.pkl
SHAP_BACKGROUND_SAMPLES=100
VEDIC_BENCHMARK_ENABLED=true

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=production
"""

with open(".env.example", "w") as f:
    f.write(env_content)

print("\n.env.example file created with template configuration.")
