"""
Create topic_model_event table for DB event logging

Revision ID: 36
Revises: 35
Create Date: 2025-08-21
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "36"
down_revision = "35"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "topic_model_event",
        sa.Column("event_id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "ts",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("repo_id", sa.Integer(), nullable=True),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event", sa.Text(), nullable=False),
        sa.Column("level", sa.Text(), server_default=sa.text("'INFO'"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["repo_id"], ["augur_data.repo.repo_id"], name="fk_tme_repo_id"
        ),
        sa.ForeignKeyConstraint(
            ["model_id"],
            ["augur_data.topic_model_meta.model_id"],
            name="fk_tme_model_id",
            ondelete="SET NULL",
        ),
        schema="augur_data",
    )
    op.create_index(
        "ix_tme_repo_ts", "topic_model_event", ["repo_id", "ts"], schema="augur_data"
    )
    op.create_index("ix_tme_event", "topic_model_event", ["event"], schema="augur_data")


def downgrade():
    op.drop_index("ix_tme_event", table_name="topic_model_event", schema="augur_data")
    op.drop_index("ix_tme_repo_ts", table_name="topic_model_event", schema="augur_data")
    op.drop_table("topic_model_event", schema="augur_data")
