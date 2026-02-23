"""fix outbox updated_at default

Revision ID: 8ee1b5a055c8
Revises: c44de773a403
Create Date: 2026-02-23 23:10

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "8ee1b5a055c8"
down_revision = "c44de773a403"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "outbox",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        server_default=sa.text("now()"),
    )


def downgrade():
    op.alter_column(
        "outbox",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        server_default=None,
    )
