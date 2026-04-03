"""rename water lab_type to water_chemistry

Revision ID: 202603160001
Revises: 33be4fe60cb5
Create Date: 2026-03-16 00:00:00.000000

'water' → 'water_chemistry', 'water & micro' → 'water_chemistry'
allowed_labs JSON-д 'water' → 'water_chemistry'
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '202603160001'
down_revision = '33be4fe60cb5'
branch_labels = None
depends_on = None


def upgrade():
    # Sample table: lab_type column
    op.execute(
        "UPDATE sample SET lab_type = 'water_chemistry' WHERE lab_type = 'water'"
    )
    op.execute(
        "UPDATE sample SET lab_type = 'water_chemistry', sample_type = 'water_chemistry' "
        "WHERE lab_type = 'water & micro'"
    )
    # Sample table: sample_type column (mirrors lab_type)
    op.execute(
        "UPDATE sample SET sample_type = 'water_chemistry' WHERE sample_type = 'water'"
    )
    op.execute(
        "UPDATE sample SET sample_type = 'water_chemistry' WHERE sample_type = 'water & micro'"
    )

    # AnalysisType table
    op.execute(
        "UPDATE analysis_type SET lab_type = 'water_chemistry' WHERE lab_type = 'water'"
    )

    # Chemical table
    op.execute(
        "UPDATE chemical SET lab_type = 'water_chemistry' WHERE lab_type = 'water'"
    )

    # LabReport table
    op.execute(
        "UPDATE lab_report SET lab_type = 'water_chemistry' WHERE lab_type = 'water'"
    )

    # ReportSignature table
    op.execute(
        "UPDATE report_signature SET lab_type = 'water_chemistry' WHERE lab_type = 'water'"
    )

    # User.allowed_labs (JSON array) — replace 'water' with 'water_chemistry'
    op.execute(
        """
        UPDATE "user"
        SET allowed_labs = (
            SELECT jsonb_agg(
                CASE WHEN elem = 'water' THEN 'water_chemistry'::text ELSE elem END
            )
            FROM jsonb_array_elements_text(allowed_labs::jsonb) AS elem
        )::json
        WHERE allowed_labs::text LIKE '%"water"%'
        """
    )


def downgrade():
    op.execute(
        "UPDATE sample SET lab_type = 'water' WHERE lab_type = 'water_chemistry'"
    )
    op.execute(
        "UPDATE sample SET sample_type = 'water' WHERE sample_type = 'water_chemistry'"
    )
    op.execute(
        "UPDATE analysis_type SET lab_type = 'water' WHERE lab_type = 'water_chemistry'"
    )
    op.execute(
        "UPDATE chemical SET lab_type = 'water' WHERE lab_type = 'water_chemistry'"
    )
    op.execute(
        "UPDATE lab_report SET lab_type = 'water' WHERE lab_type = 'water_chemistry'"
    )
    op.execute(
        "UPDATE report_signature SET lab_type = 'water' WHERE lab_type = 'water_chemistry'"
    )
    op.execute(
        """
        UPDATE "user"
        SET allowed_labs = (
            SELECT jsonb_agg(
                CASE WHEN elem = 'water_chemistry' THEN 'water'::text ELSE elem END
            )
            FROM jsonb_array_elements_text(allowed_labs::jsonb) AS elem
        )::json
        WHERE allowed_labs::text LIKE '%"water_chemistry"%'
        """
    )
