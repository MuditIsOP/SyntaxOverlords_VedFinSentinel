"""Check database tables"""
import asyncio
from app.db.session import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
        tables = [x[0] for x in result.fetchall()]
        print(f"Tables found: {tables}")
        
        for tbl in tables:
            try:
                r = await conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
                cnt = r.scalar()
                print(f"  {tbl}: {cnt} rows")
            except Exception as e:
                print(f"  {tbl}: ERROR - {e}")

asyncio.run(check())
