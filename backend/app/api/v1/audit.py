from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
import io
import csv
from typing import List, Optional
import uuid

from app.models.risk_audit_log import RiskAuditLog
from app.models.base import RiskBandEnum
from app.db.session import get_db_session

from app.services.compliance import generate_compliance_report
from app.core.dependencies import VerifiedToken

router = APIRouter()

@router.get("/audit/logs", summary="Fetch Historical Audit Logs")
async def get_audit_logs(
    token: VerifiedToken,
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(100, le=1000),
    offset: int = 0,
    risk_band: Optional[str] = None,
):
    """Retrieves paginated audit logs for compliance review."""
    stmt = select(RiskAuditLog).order_by(desc(RiskAuditLog.created_at))
    
    if risk_band:
        try:
            band_enum = RiskBandEnum[risk_band.upper()]
            stmt = stmt.filter_by(risk_band=band_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid risk band")
            
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/audit/export", summary="Export Audit Logs (CSV/PDF)")
async def export_audit_logs(
    token: VerifiedToken,
    format: str = Query("csv", regex="^(csv|pdf)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Exports immutable audit trails for regulatory compliance.
    Current implementation streams CSV; PDF is now functional.
    """
    stmt = select(RiskAuditLog).order_by(desc(RiskAuditLog.created_at)).limit(500)
    if start_date:
        stmt = stmt.where(RiskAuditLog.created_at >= start_date)
    if end_date:
        stmt = stmt.where(RiskAuditLog.created_at <= end_date)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    # Convert to list of dicts for generator
    log_dicts = []
    for l in logs:
        log_dicts.append({
            "txn_id": str(l.txn_id),
            "risk_band": l.risk_band.name if l.risk_band else "UNKNOWN",
            "fraud_score": float(l.fraud_score),
            "action_taken": l.action_taken.name if l.action_taken else "N/A",
            "created_at": l.created_at.isoformat() if l.created_at else ""
        })
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["txn_id", "risk_band", "fraud_score", "action_taken", "created_at"])
        writer.writeheader()
        writer.writerows(log_dicts)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_export.csv"}
        )
    else:
        pdf_buffer = generate_compliance_report(log_dicts)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Sentinel_Audit_{datetime.now().strftime('%Y%H%M')}.pdf"}
        )

