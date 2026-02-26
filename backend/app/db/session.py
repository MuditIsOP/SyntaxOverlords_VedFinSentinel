import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

logger = structlog.get_logger()

# Use DATABASE_URL from settings (PostgreSQL primary, can be overridden via .env)
_db_url = settings.DATABASE_URL

# Detect if we need to fall back to SQLite
_using_fallback = False
if "postgresql" in _db_url:
    try:
        import asyncpg  # noqa: F401
    except ImportError:
        logger.warning("asyncpg_not_installed", fallback="sqlite")
        _db_url = "sqlite+aiosqlite:///./vedfin_local.db"
        _using_fallback = True

engine = create_async_engine(_db_url, echo=False)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

# Alias for compatibility with ws.py
async_session_factory = async_session_maker


async def get_db_session():
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Create all tables if they don't exist."""
    from app.models.base import Base
    import app.models.user
    import app.models.transaction
    import app.models.risk_audit_log

    # If PostgreSQL is unreachable, fall back to SQLite
    global engine, async_session_maker, _using_fallback
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        if not _using_fallback:
            logger.info("database_connected", driver="postgresql")
        else:
            logger.info("database_connected", driver="sqlite_fallback")
    except Exception as e:
        if not _using_fallback:
            logger.warning("postgresql_unreachable", error=str(e), fallback="sqlite")
            _db_url_fallback = "sqlite+aiosqlite:///./vedfin_local.db"
            engine = create_async_engine(_db_url_fallback, echo=False)
            async_session_maker = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
            )
            _using_fallback = True
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("database_connected", driver="sqlite_fallback")
        else:
            raise
