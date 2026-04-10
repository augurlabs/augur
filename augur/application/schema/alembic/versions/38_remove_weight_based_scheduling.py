"""Remove weight-based scheduling columns

Revision ID: 38
Revises: 37
Create Date: 2026-01-10 02:52:00.000000

This migration removes the legacy weight-based scheduling system columns
from the collection_status table. These columns are no longer used for
scheduling repository collection tasks.

Related to issue #3267
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38'
down_revision = '37'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the weight-based scheduling columns that are no longer in use.
    # We are keeping 'issue_pr_sum' and 'commit_sum' because they are still used 
    # for ordering repositories and checking facade status.
    op.drop_column('collection_status', 'core_weight', schema='augur_operations')
    op.drop_column('collection_status', 'facade_weight', schema='augur_operations')
    op.drop_column('collection_status', 'secondary_weight', schema='augur_operations')
    op.drop_column('collection_status', 'ml_weight', schema='augur_operations')


def downgrade():
    # Restore the weight columns if we ever need to revert.
    # Note: The data originally in these columns will be lost upon downgrade as it was nullified.
    op.add_column('collection_status', sa.Column('core_weight', sa.BigInteger(), nullable=True), schema='augur_operations')
    op.add_column('collection_status', sa.Column('facade_weight', sa.BigInteger(), nullable=True), schema='augur_operations')
    op.add_column('collection_status', sa.Column('secondary_weight', sa.BigInteger(), nullable=True), schema='augur_operations')
    op.add_column('collection_status', sa.Column('ml_weight', sa.BigInteger(), nullable=True), schema='augur_operations')
