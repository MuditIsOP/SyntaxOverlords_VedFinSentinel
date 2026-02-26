"""
Database migration script to update schema:
- Remove vedic_checksum and vedic_valid columns
- Add integrity_hash, integrity_valid, and structural_anomalies columns
- Update RiskAuditLog to replace nikhilam_threshold with dynamic_threshold
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'remove_vedic_add_integrity'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Update transactions table
    # Add new columns
    op.add_column('transactions', sa.Column('integrity_hash', sa.String(256), nullable=True))
    op.add_column('transactions', sa.Column('integrity_valid', sa.Boolean(), nullable=True, default=True))
    op.add_column('transactions', sa.Column('structural_anomalies', sa.JSON(), nullable=True))
    
    # Remove old columns
    op.drop_column('transactions', 'vedic_checksum')
    op.drop_column('transactions', 'vedic_valid')
    
    # Update risk_audit_logs table
    op.add_column('risk_audit_logs', sa.Column('dynamic_threshold', sa.Numeric(12, 4), nullable=True))
    op.drop_column('risk_audit_logs', 'nikhilam_threshold')
    
    print("✅ Migration completed: Removed Vedic columns, added cryptographic integrity columns")


def downgrade():
    # Reverse the migration
    op.add_column('transactions', sa.Column('vedic_checksum', sa.String(128), nullable=True))
    op.add_column('transactions', sa.Column('vedic_valid', sa.Boolean(), nullable=True, default=True))
    
    op.drop_column('transactions', 'integrity_hash')
    op.drop_column('transactions', 'integrity_valid')
    op.drop_column('transactions', 'structural_anomalies')
    
    op.add_column('risk_audit_logs', sa.Column('nikhilam_threshold', sa.Numeric(12, 4), nullable=True))
    op.drop_column('risk_audit_logs', 'dynamic_threshold')
