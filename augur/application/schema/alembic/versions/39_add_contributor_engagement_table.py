"""Add contributor_engagement table

Revision ID: 39
Revises: 38
Create Date: 2025-07-26 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "39"
down_revision = "38"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contributor_engagement",
        sa.Column("engagement_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("repo_id", sa.BigInteger(), nullable=False),
        sa.Column("cntrb_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("platform", sa.String(), nullable=True),
        # D0 Level - Basic Engagement
        sa.Column(
            "d0_forked", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
        sa.Column(
            "d0_starred_or_watched",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column("d0_engagement_timestamp", sa.TIMESTAMP, nullable=True),
        # D1 Level - Issue/Review Engagement
        sa.Column("d1_first_issue_created_at", sa.TIMESTAMP, nullable=True),
        sa.Column("d1_first_pr_opened_at", sa.TIMESTAMP, nullable=True),
        sa.Column("d1_first_pr_commented_at", sa.TIMESTAMP, nullable=True),
        # D2 Level - Significant Contributions
        sa.Column(
            "d2_has_merged_pr",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "d2_created_many_issues",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "d2_total_comments",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=True,
        ),
        sa.Column(
            "d2_has_pr_with_many_commits",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "d2_commented_on_multiple_prs",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        # Metadata
        sa.Column("tool_source", sa.String(), nullable=True),
        sa.Column("tool_version", sa.String(), nullable=True),
        sa.Column("data_source", sa.String(), nullable=True),
        sa.Column(
            "data_collection_date",
            sa.TIMESTAMP,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["repo_id"],
            ["augur_data.repo.repo_id"],
            name="fk_contributor_engagement_repo",
        ),
        sa.ForeignKeyConstraint(
            ["cntrb_id"],
            ["augur_data.contributors.cntrb_id"],
            name="fk_contributor_engagement_contributors",
        ),
        sa.PrimaryKeyConstraint("engagement_id"),
        schema="augur_data",
    )


def downgrade():
    op.drop_table("contributor_engagement", schema="augur_data")
