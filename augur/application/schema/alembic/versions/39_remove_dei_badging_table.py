"""Remove DEI Badging table

Revision ID: 39
Revises: 38
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39'
down_revision = '38'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('dei_badging', schema='augur_data')


def downgrade():
    op.create_table('dei_badging',
        sa.Column('id', sa.Integer, nullable=False, autoincrement=True),
        sa.Column('badging_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('repo_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['repo_id'], ['augur_data.repo.repo_id'], name='user_repo_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', 'repo_id'),
        schema='augur_data'
    )
