"""Create topic_model_meta table

Revision ID: 35
Revises: 34
Create Date: 2024-08-28 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '35'
down_revision = '34'
branch_labels = None
depends_on = None


def upgrade():
    # Create topic_model_meta table based on ER diagram with NOT NULL constraints
    op.create_table('topic_model_meta',
        # Primary key
        sa.Column('model_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        
        # Foreign key to repo (nullable for multi-repo training)
        sa.Column('repo_id', sa.Integer(), nullable=True),
        
        # Model metadata (all NOT NULL as requested)
        sa.Column('model_method', sa.String(), nullable=False),
        sa.Column('num_topics', sa.Integer(), nullable=False),
        sa.Column('num_words_per_topic', sa.Integer(), nullable=False),
        
        # Parameters and configuration (NOT NULL)
        sa.Column('training_parameters', postgresql.JSONB(), nullable=False),
        sa.Column('model_file_paths', postgresql.JSONB(), nullable=False),
        sa.Column('parameters_hash', sa.String(), nullable=False),
        
        # Quality metrics (NOT NULL, but can use default values)
        sa.Column('coherence_score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('perplexity_score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('topic_diversity', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('quality', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        
        # Training metadata (NOT NULL)
        sa.Column('training_message_count', sa.BigInteger(), nullable=False),
        sa.Column('data_fingerprint', postgresql.JSONB(), nullable=False),
        
        # Visualization data (optional)
        sa.Column('visualization_data', postgresql.JSONB(), nullable=True),
        
        # Timestamps (NOT NULL with defaults)
        sa.Column('training_start_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('training_end_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('data_collection_date', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Standard Augur metadata (NOT NULL)
        sa.Column('tool_source', sa.String(), nullable=False),
        sa.Column('tool_version', sa.String(), nullable=False),
        sa.Column('data_source', sa.String(), nullable=False),
        
        # Constraints
        sa.ForeignKeyConstraint(['repo_id'], ['augur_data.repo.repo_id'], ),
        sa.PrimaryKeyConstraint('model_id'),
        schema='augur_data'
    )


def downgrade():
    op.drop_table('topic_model_meta', schema='augur_data') 