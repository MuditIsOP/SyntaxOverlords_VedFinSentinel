import asyncio
import sys
import os

# Ensure we are in the backend directory context if needed
# But usually the run_command Cwd handles this.
# If Cwd is D:\Utkarsh, we need to add 'backend' to sys.path

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import async_session_maker
from app.services.metrics import compute_dashboard_metrics

async def test_metrics():
    # Import models to register them with Base.metadata
    from app.models.base import Base
    import app.models.user
    import app.models.transaction
    import app.models.risk_audit_log

    try:
        async with async_session_maker() as session:
            metrics = await compute_dashboard_metrics(session)
            print("SUCCESS")
            # print(metrics) # Just check success for now
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_metrics())
