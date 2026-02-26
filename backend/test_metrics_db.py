import asyncio
from app.db.session import async_session_maker
from app.services.metrics import compute_dashboard_metrics

async def test_metrics():
    try:
        async with async_session_maker() as session:
            metrics = await compute_dashboard_metrics(session)
            print("SUCCESS")
            print(metrics)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_metrics())
