#SPDX-License-Identifier: MIT
import click
import subprocess
import os
import sys
import logging
from sqlalchemy import text, func

from augur.application.cli import with_database
from augur.application.db.models import Repo, CollectionStatus
from augur.application.db.models.augur_operations import WorkerOauth
from augur.application.db.session import DatabaseSession

logger = logging.getLogger(__name__)

@click.group("verify", short_help="Verify system status and diagnostics")
def cli():
    pass

@cli.command("system")
@with_database
@click.pass_context
def verify_system(ctx):
    """Check general system status."""
    print("Verifying System Status...")
    
    # Check Version
    try:
        import metadata
        print(f"Augur Version: {metadata.__version__}")
    except ImportError:
        try:
            # Try importing from augur.metadata if installed as package
            from augur import metadata
            print(f"Augur Version: {metadata.__version__}")
        except ImportError:
            # Fallback to file read
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                meta_path = os.path.join(base_dir, "metadata.py")
                if os.path.exists(meta_path):
                    with open(meta_path, "r") as f:
                        for line in f:
                            if "__version__" in line:
                                print(f"Augur Version: {line.split('=')[1].strip().strip('\"').strip(\"'\")}")
                                break
                else:
                    print("Augur Version: Unknown (metadata.py not found)")
            except Exception as e:
                print(f"Augur Version: Unknown ({e})")

    # Check Docker
    if os.path.exists('/.dockerenv'):
        print("Environment: Docker")
    else:
        print("Environment: Standard (Non-Docker)")
        
    # Check API Keys
    try:
        with DatabaseSession(logger, engine=ctx.obj.engine) as session:
            oauth_count = session.query(WorkerOauth).count()
            print(f"API Keys Loaded: {oauth_count}")
            
            gh_keys = session.query(WorkerOauth).filter(WorkerOauth.platform == 'github').count()
            gl_keys = session.query(WorkerOauth).filter(WorkerOauth.platform == 'gitlab').count()
            print(f"  - GitHub: {gh_keys}")
            print(f"  - GitLab: {gl_keys}")
    except Exception as e:
        print(f"Error checking API keys: {e}")

@cli.command("db")
@with_database
@click.pass_context
def verify_db(ctx):
    """Check database health and migrations."""
    print("Verifying Database...")
    
    # 1. Migrations
    print("\n[Migrations]")
    try:
        # This assumes alembic is in path
        print("Checking alembic current revision...")
        try:
             current = subprocess.check_output(["alembic", "current"], stderr=subprocess.STDOUT, text=True).strip()
             print(f"Current Output: {current}")
        except subprocess.CalledProcessError as e:
             current = f"Error: {e.output}"
             print(current)

        # Check for pending migrations
        # alembic history | head might be useful but we can use dry run upgrade maybe?
        # or just check output of alembic current to see if it says '(head)' or similar implied
        pass
             
    except Exception as e:
        print(f"Error checking migrations: {e}")

    with DatabaseSession(logger, engine=ctx.obj.engine) as session:
        # 2. Duplicate Repos
        print("\n[Duplicate Repos Check]")
        try:
            # Find repo_src_ids that appear more than once (excluding nulls)
            duplicates = session.query(Repo.repo_src_id, func.count(Repo.repo_id))\
                .filter(Repo.repo_src_id != None)\
                .group_by(Repo.repo_src_id)\
                .having(func.count(Repo.repo_id) > 1).all()
                
            if not duplicates:
                print("No duplicate repositories found by repo_src_id.")
            else:
                print(f"Found {len(duplicates)} sets of duplicate repos:")
                for src_id, count in duplicates:
                    print(f"  repo_src_id: {src_id} (Count: {count})")
        except Exception as e:
             print(f"Error checking duplicates: {e}")
        
        # 3. Misspelled columns check
        print("\n[Schema Health]")
        try:
             # Check for repo_deps_libyear data_collection_data issue
             res = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'repo_deps_libyear' AND column_name LIKE 'data_collection_%'")).fetchall()
             columns = [r[0] for r in res]
             misspelled = False
             for col in columns:
                 if "data" in col and "date" not in col: # e.g. data_collection_data
                     print(f"WARNING: Potential misspelling in repo_deps_libyear: {col}. This may affect future migrations.")
                     misspelled = True
             if not misspelled:
                 print("repo_deps_libyear columns look correct.")
        except Exception as e:
            print(f"Could not verify schema columns: {e}")

        # 4. Table Bloat
        print("\n[Table Bloat Check]")
        try:
            # Simple check for dead tuples ratio using pg_stat_user_tables
            # Use text() to safely execute raw SQL
            query = text("""
                SELECT schemaname, relname, n_live_tup, n_dead_tup, 
                CASE WHEN n_live_tup > 0 THEN n_dead_tup::float / n_live_tup::float ELSE 0 END as bloat_ratio 
                FROM pg_stat_user_tables 
                WHERE n_dead_tup > 1000 
                ORDER BY bloat_ratio DESC 
                LIMIT 10
            """)
            bloat_res = session.execute(query).fetchall()
            
            if not bloat_res:
                 print("No significant table bloat detected (tables with > 1000 dead tuples).")
            else:
                 print("Top 10 bloated tables (by dead tuple ratio, > 1000 dead tuples):")
                 print(f"{'Table':<40} {'Live':<10} {'Dead':<10} {'Ratio':<10}")
                 for row in bloat_res:
                     # row is simpler to access by index or name
                     table = f"{row[0]}.{row[1]}"
                     ratio = f"{row[4]:.2%}"
                     print(f"{table:<40} {row[2]:<10} {row[3]:<10} {ratio:<10}")
        except Exception as e:
            print(f"Error checking table bloat: {e}")


@cli.command("collection")
@with_database
@click.pass_context
def verify_collection(ctx):
    """Verify collection status."""
    print("Verifying Collection Status...")
    
    with DatabaseSession(logger, engine=ctx.obj.engine) as session:
        # Counts
        total_repos = session.query(Repo).count()
        print(f"Total Configured Repos: {total_repos}")
        
        # Collected today
        print("\n[Collection Phases - Last 24 Hours]")
        
        for phase, col in [("Core", CollectionStatus.core_data_last_collected),
                           ("Secondary", CollectionStatus.secondary_data_last_collected),
                           ("Facade", CollectionStatus.facade_data_last_collected)]:
            try:
                # PostGres specific interval
                count = session.query(CollectionStatus).filter(col >= text("NOW() - INTERVAL '24 HOURS'")).count()
                print(f"  {phase}: {count} repos collected")
            except Exception as e:
                 print(f"  {phase}: Error querying ({e})")

        # Collection Status counts
        print("\n[Current Status Counts]")
        for status_col, name in [(CollectionStatus.core_status, "Core"),
                                 (CollectionStatus.secondary_status, "Secondary"),
                                 (CollectionStatus.facade_status, "Facade")]:
             
             print(f"  {name}:")
             try:
                 stats = session.query(status_col, func.count(CollectionStatus.repo_id))\
                     .group_by(status_col).all()
                 for status, count in stats:
                     print(f"    {status}: {count}")
             except Exception as e:
                 print(f"    Error: {e}")

@cli.command("all")
@click.pass_context
def verify_all(ctx):
    """Run all verification checks."""
    ctx.invoke(verify_system)
    ctx.invoke(verify_db)
    ctx.invoke(verify_collection)
