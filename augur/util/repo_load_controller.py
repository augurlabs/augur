import logging

import base64

from typing import Any, Dict

from augur.application.db.engine import DatabaseEngine
from augur.application.db.models import Repo, UserRepo, RepoGroup, UserGroup, User, CollectionStatus
from augur.application.db.models.augur_operations import retrieve_owner_repos
from augur.application.db.util import execute_session_query

from sqlalchemy import Column, Table, MetaData, or_
from sqlalchemy.sql.operators import ilike_op
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.orm import Query


logger = logging.getLogger(__name__)


with DatabaseEngine() as engine:
    augur_data_schema = MetaData(schema = "augur_data")
    augur_data_schema.reflect(bind = engine, views = True)
    
    commits_materialized_view: Table = augur_data_schema.tables["augur_data.api_get_all_repos_commits"]
    issues_materialized_view: Table = augur_data_schema.tables["augur_data.api_get_all_repos_issues"]


class RepoLoadController:

    def __init__(self, gh_session):
        self.session = gh_session


    def add_cli_repo(self, repo_data: Dict[str, Any], from_org_list=False, repo_type=None):
        """Add list of repos to specified repo_groups

        Args:
            url_data: dict with repo_group_id and repo urls
        """

        # if the repo is from an org list then 
        # the repo type must be passed in
        # so we don't have to hit an endpoint 
        # for every repo to get its type
        if from_org_list and not repo_type:
            return False, {"status": "Repo type must be passed if the repo is from an organization's list of repos"}

        url = repo_data["url"]
        repo_group_id = repo_data["repo_group_id"]

        # if it is from not from an org list then we need to check its validity, and get the repo type
        if not from_org_list:
            if "gitlab" in url:
                result = Repo.is_valid_gitlab_repo(self.session, url)
            else:
                result = Repo.is_valid_github_repo(self.session, url)
            if not result[0]:
                return False, {"status": result[1]["status"], "repo_url": url}
            
            try:
                repo_type = result[1]["repo_type"]
            except KeyError:
                print("Skipping repo type...")


        # if the repo doesn't exist it adds it
        if "gitlab" in url:
            repo_id = Repo.insert_gitlab_repo(self.session, url, repo_group_id, "CLI")
            CollectionStatus.insert(self.session, logger, repo_id)
        else:
            repo_id = Repo.insert_github_repo(self.session, url, repo_group_id, "CLI", repo_type)
            CollectionStatus.insert(self.session, logger, repo_id)

        if not repo_id:
            logger.warning(f"Invalid repo group id specified for {url}, skipping.")
            return False, {"status": f"Invalid repo group id specified for {url}, skipping."}

        UserRepo.insert(self.session, repo_id)

        #collection_status records are now only added during collection -IM 5/1/23
        #CollectionStatus.insert(self.session, repo_id)

        return True, {"status": "Repo added", "repo_url": url}

    def add_cli_org(self, org_name):
        """Add list of orgs and their repos to specified repo_groups

        Args:
            org_data: dict with repo_group_id and org urls
        """
        
        result = retrieve_owner_repos(self.session, org_name)
        repos = result[0]
        type = result[1]["owner_type"]
        if not repos:
            print(
                f"No organization with name {org_name} could be found")
            return {"status": "No organization found"}

        # check if the repo group already exists
        query = self.session.query(RepoGroup).filter(RepoGroup.rg_name == org_name)
        rg = execute_session_query(query, 'first')
        if rg:
            print(f"{rg.rg_name} is already a repo group")

            return {"status": "Already a repo group"}

        print(f'Organization "{org_name}" found')

        rg = RepoGroup(rg_name=org_name, rg_description="", rg_website="", rg_recache=0, rg_type="Unknown",
                    tool_source="Loaded by user", tool_version="1.0", data_source="Git")
        self.session.add(rg)
        self.session.commit()
        repo_group_id = rg.repo_group_id
        print(f"{org_name} repo group created")

        for repo_url in repos:
            print(f"Adding {repo_url}")
            result, status = self.add_cli_repo({"url": repo_url, "repo_group_id": repo_group_id}, from_org_list=True, repo_type=type)
            if not result:
                print(status["status"])

        return {"status": "Org added"}


    def paginate_repos(self, source, page=0, page_size=25, sort="repo_id", direction="ASC", **kwargs):

        if not source:
            print("Func: paginate_repos. Error: Source Required")
            return None, {"status": "Source Required"}

        if source not in ["all", "user", "group"]:
            print("Func: paginate_repos. Error: Invalid source")
            return None, {"Invalid source"}

        if direction and direction != "ASC" and direction != "DESC":
            print("Func: paginate_repos. Error: Invalid direction")
            return None, {"status": "Invalid direction"}

        try:
            page = int(page) if page else 0
            page_size = int(page_size) if page else 25
        except TypeError:
            print("Func: paginate_repos. Error: Page size and page should be integers")
            return None, {"status": "Page size and page should be integers"}

        if page < 0 or page_size < 0:
            print("Func: paginate_repos. Error: Page size and page should be positive")
            return None, {"status": "Page size and page should be postive"}

        order_by = sort if sort else "repo_id"
        order_direction = direction if direction else "ASC"


        query, result = self.generate_repo_query(source, count=False, order_by=order_by, direction=order_direction, 
                                    page=page, page_size=page_size, **kwargs)


        # query, query_args, result = self.generate_repo_query(source, count=False, order_by=order_by, direction=order_direction, 
        #                             page=page, page_size=page_size, **kwargs)
        if not query:
            return None, {"status": result["status"]}

        if result["status"] == "No data":
            return [], {"status": "No data"}

        # get_page_of_repos_sql = s.sql.text(query)

        # with DatabaseEngine(connection_pool_size=1).connect() as conn:

        #     results = pd.read_sql(get_page_of_repos_sql, conn, params=query_args)

        results = [dict(x._mapping) for x in query]

        for row in results:

            row["url"] = row["url"].split('//')[1]
            row["base64_url"] = base64.b64encode(row["url"].encode())

        return results, {"status": "success"}

    def get_repo_count(self, source, **kwargs):

        if not source:
            print("Func: get_repo_count. Error: Source Required")
            return None, {"status": "Source Required"}

        if source not in ["all", "user", "group"]:
            print("Func: get_repo_count. Error: Invalid source")
            return None, {"status": "Invalid source"}
        
        query, result = self.generate_repo_query(source, count=True, **kwargs)
        if not query:
            return None, result

        if result["status"] == "No data":
            return 0, {"status": "No data"}
        
        count = query.count()
            
        return count, {"status": "success"}

    def generate_repo_query(self, source, count, **kwargs):
        
        columns: list[Column] = [
            Repo.repo_id.distinct().label("repo_id"),
            Repo.description.label("description"),
            Repo.repo_git.label("url"),
            coalesce(commits_materialized_view.columns.commits_all_time, 0).label("commits_all_time"),
            coalesce(issues_materialized_view.columns.issues_all_time, 0).label("issues_all_time"),
            RepoGroup.rg_name.label("rg_name"),
            Repo.repo_git.regexp_replace('.*github\.com\/[A-Za-z0-9 \- _]+\/([A-Za-z0-9 \- _ .]+)$', "\\1").label("repo_name"),
            Repo.repo_git.regexp_replace('.*github\.com\/([A-Za-z0-9 \- _]+)\/[A-Za-z0-9 \- _ .]+$', "\\1").label("repo_owner"),
            RepoGroup.repo_group_id.label("repo_group_id")
        ]
    
        def get_colum_by_label(label: str)-> Column:
            for column in columns:
                if column.name == label:
                    return column
        
        repos: Query = self.session.query(*columns)\
            .outerjoin(commits_materialized_view, Repo.repo_id == commits_materialized_view.columns.repo_id)\
            .outerjoin(issues_materialized_view, Repo.repo_id == issues_materialized_view.columns.repo_id)\
            .join(RepoGroup, Repo.repo_group_id == RepoGroup.repo_group_id)
        
        if source == "user":
            user: User = kwargs.get("user")
            
            if not user:
                return None, {"status": "User not passed when trying to get user repos"}
            if not user.groups:
                return None, {"status": "No data"}
            
            repos = repos.join(UserRepo, Repo.repo_id == UserRepo.repo_id)\
                .join(UserGroup, UserGroup.group_id == UserRepo.group_id)\
                .filter(UserGroup.user_id == user.user_id)
        
        elif source == "group":
            user: User = kwargs.get("user")
            
            if not user:
                return None, {"status": "User not specified"}
            group_name = kwargs.get("group_name")
            if not group_name:
                return None, {"status": "Group name not specified"}
            
            group_id = UserGroup.convert_group_name_to_id(self.session, user.user_id, group_name)
            if group_id is None:
                return None, {"status": "Group does not exists"}
            
            repos = repos.join(UserRepo, Repo.repo_id == UserRepo.repo_id)\
                .filter(UserRepo.group_id == group_id)
        
        search = kwargs.get("search")
        qkey = kwargs.get("query_key") or ["repo_name", "repo_owner"]
        if search:
            if isinstance(qkey, list) and len(qkey) > 0:
                repos = repos.filter(or_(ilike_op(get_colum_by_label(filter_column), f"%{search}%") for filter_column in qkey))
            else:
                repos = repos.filter(ilike_op(get_colum_by_label(qkey), f"%{search}%"))
        
        page_size: int = kwargs.get("page_size") or 25
        if count:
            return repos, {"status": "success"}
        else: 
            page: int = kwargs.get("page") or 0
            offset = page * page_size
            direction = kwargs.get("direction") or "ASC"
            order_by = kwargs.get("order_by") or "repo_id"
            
            if direction not in ["ASC", "DESC"]:
                return None, {"status": "Invalid direction"}
            
            if order_by not in ["repo_id", "repo_name", "repo_owner", "commits_all_time", "issues_all_time"]:
                return None, {"status": "Invalid order by"}
            
            # Find the column named in the 'order_by', and get its asc() or desc() method 
            directive = getattr(get_colum_by_label(order_by), direction.lower())
            
            repos = repos.order_by(directive())

        return repos.slice(offset, offset + page_size), {"status": "success"}

