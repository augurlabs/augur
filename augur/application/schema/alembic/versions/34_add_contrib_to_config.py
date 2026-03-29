"""Add Facade contributor full recollect to config, default to off (0) 

Revision ID: 34
Revises: 33
Create Date: 2025-10-09 12:03:57.171011

"""
from alembic import op
from augur.application.db.session import DatabaseSession
from augur.application.config import *
from sqlalchemy.sql import text
import logging

# revision identifiers, used by Alembic.
revision = '34'
down_revision = '33'
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

def upgrade():

    with DatabaseSession(logger) as session:
        config = AugurConfig(logger,session)
        config_dict = config.load_config()

        #Update the missing fields of the facade section in the config
        section = config_dict.get("Facade")

        #Just copy the default if section doesn't exist.
        if section:
            if 'facade_contributor_full_recollect' not in section.keys():
                section['facade_contributor_full_recollect'] = 0
            
        else:
            section = config.default_config["Facade"]
        
        config.add_section_from_json("Facade", section)


def downgrade():

    conn = op.get_bind()

    conn.execute(text(f"""
        DELETE FROM augur_operations.config
        WHERE section_name='Facade' AND (setting_name='facade_contributor_full_recollect');
    """))

    try:
        conn.execute(text(f"""
            DELETE FROM augur_operations.config
            WHERE section_name='Facade' AND (setting_name='facade_contributor_full_recollect');
        """))
    except:
        pass