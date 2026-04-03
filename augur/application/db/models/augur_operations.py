# encoding: utf-8
from sqlalchemy import BigInteger, SmallInteger, Column, Index, Integer, String, Table, text, UniqueConstraint, Boolean, ForeignKey, update, CheckConstraint, Sequence
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from typing import List

import logging
import secrets
import traceback

from augur.application.db.models import Repo, RepoGroup
from augur.application.db.session import DatabaseSession
from augur.application.db.models.base import Base

FRONTEND_REPO_GROUP_NAME = "Frontend Repos"
logger = logging.getLogger(__name__)

def retrieve_owner_repos(session, owner: str) -> List[str]:
    """Get the repos for an org.

    Note:
        If the org url is not valid it will return []

    Args:
        url: org url

    Returns
        List of valid repo urls or empty list if invalid org
    """
    from augur.tasks.github.util.github_data_access import GithubDataAccess, UrlNotFoundException

    OWNER_INFO_ENDPOINT = f"https://api.github.com/users/{owner}"
    ORG_REPOS_ENDPOINT = f"https://api.github.com/orgs/{owner}/repos?per_page=100"
    USER_REPOS_ENDPOINT = f"https://api.github.com/users/{owner}/repos?per_page=100"

    github_data_access = GithubDataAccess(session.oauths, logger)

    if not session.oauths.list_of_keys:
        return None, {"status": "No valid github api keys to retrieve data with"}

    # determine whether the owner is a user or an organization
    try: 
        data = github_data_access.get_resource(OWNER_INFO_ENDPOINT)
    except UrlNotFoundException as e:
        logger.error("Owner not found on github")
        return None, {"status": "Invalid owner"}
    except Exception as e:
        logger.error(f"Failed to get owner data from github. Exception: {e}")
        return None, {"status": "Failed to get owner data from github"}

    owner_type = data["type"]

    if owner_type == "User":
        url = USER_REPOS_ENDPOINT
    elif owner_type == "Organization":
        url = ORG_REPOS_ENDPOINT
    else:
        return None, {"status": f"Invalid owner type: {owner_type}"}

    # collect repo urls for the given owner
    repos = list(github_data_access.paginate_resource(url))

    repo_urls = [repo["html_url"] for repo in repos]

    return repo_urls, {"status": "success", "owner_type": owner_type}


metadata = Base.metadata

t_all = Table(
    "all",
    metadata,
    Column("Name", String),
    Column("Bytes", String),
    Column("Lines", String),
    Column("Code", String),
    Column("Comment", String),
    Column("Blank", String),
    Column("Complexity", String),
    Column("Count", String),
    Column("WeightedComplexity", String),
    Column("Files", String),
    schema="augur_operations",
)


class AugurSetting(Base):
    __tablename__ = "augur_settings"
    __table_args__ = {
        "schema": "augur_operations",
        "comment": "Augur settings include the schema version, and the Augur API Key as of 10/25/2020. Future augur settings may be stored in this table, which has the basic structure of a name-value pair. ",
    }

    id = Column(
        BigInteger,
        Sequence("augur_settings_id_seq", start=1, schema="augur_operations"),
        primary_key=True,
        server_default=text(
            "nextval('augur_operations.augur_settings_id_seq'::regclass)"
        ),
    )
    setting = Column(String)
    value = Column(String)
    last_modified = Column(TIMESTAMP(precision=0), server_default=text("CURRENT_DATE"))


t_repos_fetch_log = Table(
    "repos_fetch_log",
    metadata,
    Column("repos_id", Integer, nullable=False),
    Column("status", String(128), nullable=False),
    Column(
        "date",
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    Index("repos_id,statusops", "repos_id", "status"),
    schema="augur_operations",
    comment="For future use when we move all working tables to the augur_operations schema. ",
)

class WorkerHistory(Base):
    __tablename__ = "worker_history"
    __table_args__ = {
        "schema": "augur_operations",
        "comment": "This table stores the complete history of job execution, including success and failure. It is useful for troubleshooting. ",
    }

    history_id = Column(
        BigInteger,
        Sequence("gh_worker_history_history_id_seq", start=1, schema="augur_operations"),
        primary_key=True,
        server_default=text(
            "nextval('augur_operations.gh_worker_history_history_id_seq'::regclass)"
        ),
    )
    repo_id = Column(BigInteger)
    worker = Column(String(255), nullable=False)
    job_model = Column(String(255), nullable=False)
    oauth_id = Column(Integer)
    timestamp = Column(TIMESTAMP(precision=0), nullable=False)
    status = Column(String(7), nullable=False)
    total_results = Column(Integer)


class WorkerJob(Base):
    __tablename__ = "worker_job"
    __table_args__ = {
        "schema": "augur_operations",
        "comment": "This table stores the jobs workers collect data for. A job is found in the code, and in the augur.config.json under the construct of a “model”. ",
    }

    job_model = Column(String(255), primary_key=True)
    state = Column(Integer, nullable=False, server_default=text("0"))
    zombie_head = Column(Integer)
    since_id_str = Column(
        String(255), nullable=False, server_default=text("'0'::character varying")
    )
    description = Column(String(255), server_default=text("'None'::character varying"))
    last_count = Column(Integer)
    last_run = Column(
        TIMESTAMP(precision=0), server_default=text("NULL::timestamp without time zone")
    )
    analysis_state = Column(Integer, server_default=text("0"))
    oauth_id = Column(Integer, nullable=False)


class WorkerOauth(Base):
    __tablename__ = "worker_oauth"
    __table_args__ = {
        "schema": "augur_operations",
        "comment": "This table stores credentials for retrieving data from platform API’s. Entries in this table must comply with the terms of service for each platform. ",
    }

    oauth_id = Column(
        BigInteger,
        Sequence("worker_oauth_oauth_id_seq", start=1000, schema="augur_operations"),
        primary_key=True,
        server_default=text(
            "nextval('augur_operations.worker_oauth_oauth_id_seq'::regclass)"
        ),
    )
    name = Column(String(255), nullable=False)
    consumer_key = Column(String(255), nullable=False)
    consumer_secret = Column(String(255), nullable=False)
    access_token = Column(String(255), nullable=False)
    access_token_secret = Column(String(255), nullable=False)
    repo_directory = Column(String)
    platform = Column(String, server_default=text("'github'::character varying"))


class WorkerSettingsFacade(Base):
    __tablename__ = "worker_settings_facade"
    __table_args__ = {
        "schema": "augur_operations",
        "comment": "For future use when we move all working tables to the augur_operations schema. ",
    }

    id = Column(Integer, primary_key=True)
    setting = Column(String(32), nullable=False)
    value = Column(String, nullable=False)
    last_modified = Column(
        TIMESTAMP(precision=0), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


t_working_commits = Table(
    "working_commits",
    metadata,
    Column("repos_id", Integer, nullable=False),
    Column(
        "working_commit", String(40), server_default=text("'NULL'::character varying")
    ),
    schema="augur_operations",
    comment="For future use when we move all working tables to the augur_operations schema. ",
)


class Config(Base):
    __tablename__ = 'config'
    __table_args__ = (
        UniqueConstraint('section_name', "setting_name", name='unique-config-setting'),
        {"schema": "augur_operations"}
    )

    id = Column(SmallInteger, primary_key=True, nullable=False)
    section_name = Column(String, nullable=False)
    setting_name = Column(String, nullable=False)
    value = Column(String)
    type = Column(String)

    

# add admit column to database
class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('email', name='user-unique-email'),
        UniqueConstraint('login_name', name='user-unique-name'),
        UniqueConstraint('text_phone', name='user-unique-phone'),
        {"schema": "augur_operations"}
    )

    user_id = Column(Integer, primary_key=True)
    login_name = Column(String, nullable=False)
    login_hashword = Column(String, nullable=False)
    email = Column(String, nullable=False)
    text_phone = Column(String)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    admin = Column(Boolean, nullable=False)
    tool_source = Column(String)
    tool_version = Column(String)
    data_source = Column(String)
    data_collection_date = Column(TIMESTAMP(precision=0), server_default=text("CURRENT_TIMESTAMP"))
    email_verified = Column(Boolean, server_default='false', nullable=False)

    groups = relationship("UserGroup", back_populates="user")
    tokens = relationship("UserSessionToken", back_populates="user")
    applications = relationship("ClientApplication", back_populates="user")

    _is_authenticated = False
    _is_active = True
    _is_anoymous = True

    @property
    def is_authenticated(self):
        return self._is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, val):
        self._is_authenticated = val

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, val):
        self._is_active = val

    @property
    def is_anoymous(self):
        return self._is_anoymous

    @is_anoymous.setter
    def is_anoymous(self, val):
        self._is_anoymous = val

    @staticmethod
    def exists(session, username):
        return User.get_user(session, username) is not None

    def get_id(self):
        return self.login_name

    def validate(self, password) -> bool:

        if not password:
            return False

        result = check_password_hash(self.login_hashword, password)
        return result

    @staticmethod
    def get_user(session, username: str):

        if not isinstance(username, str):
            return None

        try:
            user = session.query(User).filter(User.login_name == username).one()
            return user
        except NoResultFound:
            return None
        except Exception as e:
            session.rollback()
            raise e

    @staticmethod
    def get_by_id(session, user_id: int):

        if not isinstance(user_id, int):
            return None
        try:
            user = session.query(User).filter(User.user_id == user_id).one()
            return user
        except NoResultFound:
            return None

    @staticmethod
    def create_user(username: str, password: str, email: str, first_name:str, last_name:str, admin=False):

        if username is None or password is None or email is None or first_name is None or last_name is None:
            return False, {"status": "Missing field"}

        with DatabaseSession(logger) as session:

            user = session.query(User).filter(User.login_name == username).first()
            if user is not None:
                return False, {"status": "A User already exists with that username"}

            emailCheck = session.query(User).filter(User.email == email).first()
            if emailCheck is not None:
                return False, {"status": "A User already exists with that email"}

            try:
                user = User(login_name = username, login_hashword = User.compute_hashsed_password(password), email = email, first_name = first_name, last_name = last_name, tool_source="User API", tool_version=None, data_source="API", admin=admin)
                session.add(user)
                session.commit()

                result = user.add_group("default")
                if not result[0] and result[1]["status"] != "Group already exists":
                    return False, {"status": "Failed to add default group for the user"}

                return True, {"status": "Account successfully created"}
            except AssertionError as exception_message:
                return False, {"Error": f"{exception_message}."}

    def delete(self, session):

        for group in self.groups:
            user_repos_list = group.repos

            for user_repo_entry in user_repos_list:
                session.delete(user_repo_entry)

            session.delete(group)

        session.delete(self)
        session.commit()

        return True, {"status": "User deleted"}

    def update_password(self, session, old_password, new_password):

        if not isinstance(old_password, str):
            return False, {"status": f"Invalid type {type(old_password)} passed as old_password should be type string"}

        if not isinstance(new_password, str):
            return False, {"status": f"Invalid type {type(new_password)} passed as old_password should be type string"}

        if not check_password_hash(self.login_hashword, old_password):
            return False, {"status": "Password did not match users password"}

        self.login_hashword = User.compute_hashsed_password(new_password)
        session.commit()

        return True, {"status": "Password updated"}

    def update_email(self, session, new_email):

        if not new_email:
            print("Need new email to update the email")
            return False, {"status": "Missing argument"}


        existing_user = session.query(User).filter(User.email == new_email).first()
        if existing_user is not None:
            print("Func: update_user. Error: Already an account with this email")
            return False, {"status": "There is already an account with this email"}

        self.email = new_email
        session.commit()

        return True, {"status": "Email updated"}

    def update_username(self, session, new_username):

        if not new_username:
            print("Need new username to update the username")
            return False, {"status": "Missing argument"}

        existing_user = session.query(User).filter(User.login_name == new_username).first()
        if existing_user is not None:
            print("Func: update_user. Error: Already an account with this username")
            return False, {"status": "Username already taken"}

        self.login_name = new_username
        session.commit()

        return True, {"status": "Username updated"}


    def add_group(self, group_name):

        with DatabaseSession(logger) as session:
            result = UserGroup.insert(session, self.user_id, group_name)

        return result

    def remove_group(self, group_name):

        with DatabaseSession(logger) as session:
            result = UserGroup.delete(session, self.user_id, group_name)

        return result

    def add_github_repo(self, group_name, repo_url):

        from augur.tasks.github.util.github_task_session import GithubTaskSession
        from augur.tasks.github.util.github_api_key_handler import NoValidKeysError
        try:
            with GithubTaskSession(logger) as session:
                result = UserRepo.add_github_repo(session, repo_url, self.user_id, group_name)
        except NoValidKeysError:
            return False, {"status": "No valid keys"}

        return result
    
    def add_gitlab_repo(self, group_name, repo_url):
        
        from augur.tasks.gitlab.gitlab_task_session import GitlabTaskSession
        from augur.tasks.github.util.github_api_key_handler import NoValidKeysError
        try:
            with GitlabTaskSession(logger) as session:
                result = UserRepo.add_gitlab_repo(session, repo_url, self.user_id, group_name)
        except NoValidKeysError:
            return False, {"status": "No valid keys"}

        return result


    def remove_repo(self, group_name, repo_id):

        with DatabaseSession(logger) as session:
            result = UserRepo.delete(session, repo_id, self.user_id, group_name)

        return result

    def add_github_org(self, group_name, org_url):

        from augur.tasks.github.util.github_task_session import GithubTaskSession
        from augur.tasks.github.util.github_api_key_handler import NoValidKeysError

        try:
            with GithubTaskSession(logger) as session:
                result = UserRepo.add_github_org_repos(session, org_url, self.user_id, group_name)
        except NoValidKeysError:
            return False, {"status": "No valid keys"}

        return result

    def get_groups(self):

        return self.groups, {"status": "success"}

    def get_group_names(self, search=None, reversed=False):

        user_groups = self.get_groups()[0]

        if search is None:
            group_names = [group.name for group in user_groups]
        else:
            group_names = [group.name for group in user_groups if search.lower() in group.name.lower()]

        group_names.sort(reverse = reversed)

        return group_names, {"status": "success"}

    def get_groups_info(self, search=None, reversed=False, sort="group_name"):
        (groups, result) = self.get_groups()

        if search is not None:
            groups = [group for group in groups if search.lower() in group.name.lower()]

        for group in groups:
            group.count = self.get_group_repo_count(group.name)[0]

        def sorting_function(group):
            if sort == "group_name":
                return group.name
            elif sort == "repo_count":
                return group.count
            elif sort == "favorited":
                return group.favorited

        groups = sorted(groups, key=sorting_function, reverse=reversed)

        return groups, {"status": "success"}


    def get_repos(self, page=0, page_size=25, sort="repo_id", direction="ASC", search=None):

        from augur.util.repo_load_controller import RepoLoadController

        with DatabaseSession(logger) as session:
            result = RepoLoadController(session).paginate_repos("user", page, page_size, sort, direction, user=self, search=search)

        return result

    def get_repo_count(self, search = None):
        from augur.util.repo_load_controller import RepoLoadController

        with DatabaseSession(logger) as session:
            result = RepoLoadController(session).get_repo_count(source="user", user=self, search = search)

        return result


    def get_group_repos(self, group_name, page=0, page_size=25, sort="repo_id", direction="ASC", search=None):
        from augur.util.repo_load_controller import RepoLoadController

        with DatabaseSession(logger) as session:
            result = RepoLoadController(session).paginate_repos("group", page, page_size, sort, direction, user=self, group_name=group_name, search=search)

        return result


    def get_group_repo_count(self, group_name, search = None):
        from augur.util.repo_load_controller import RepoLoadController

        with DatabaseSession(logger) as session:
            result = RepoLoadController(session).get_repo_count(source="group", group_name=group_name, user=self, search=search)

        return result

    def invalidate_session(self, token):

        with DatabaseSession(logger) as session:
            row_count = session.query(UserSessionToken).filter(UserSessionToken.user_id == self.user_id, UserSessionToken.token == token).delete()
            session.commit()

        return row_count == 1

    def delete_app(self, app_id):

        with DatabaseSession(logger) as session:
            row_count = session.query(ClientApplication).filter(ClientApplication.user_id == self.user_id, ClientApplication.id == app_id).delete()
            session.commit()

        return row_count == 1

    def add_app(self, name, redirect_url):

        with DatabaseSession(logger) as session:
            try:
                app = ClientApplication(id=secrets.token_hex(16), api_key=secrets.token_hex(), name=name, redirect_url=redirect_url, user_id=self.user_id)
                session.add(app)
                session.commit()
            except Exception as e:
                print(e)
                return False

        return True

    def toggle_group_favorite(self, group_name):

        with DatabaseSession(logger) as session:
            group = session.query(UserGroup).filter(UserGroup.name == group_name, UserGroup.user_id == self.user_id).first()
            if not group:
                return False, {"status": "Group does not exist"}

            group.favorited = not group.favorited

            session.commit()

        return True, {"status": "Success"}

    def get_favorite_groups(self, session):

        try:
            groups = session.query(UserGroup).filter(UserGroup.user_id == self.user_id, UserGroup.favorited == True).all()
        except Exception as e:
            print(f"Error while trying to get favorite groups: {e}")
            return None, {"status": "Error when trying to get favorite groups"}

        return groups, {"status": "Success"}

    @staticmethod
    def compute_hashsed_password(password):
        return generate_password_hash(password, method='pbkdf2:sha512', salt_length=32)



class UserGroup(Base):
    __tablename__ = 'user_groups'
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='user_groups_user_id_name_key'),
        {"schema": "augur_operations"}
    )
    
    group_id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer,
                    ForeignKey("augur_operations.users.user_id", name="user_group_user_id_fkey"), nullable=False
    )
    name = Column(String, nullable=False)
    favorited = Column(Boolean, nullable=False, server_default=text("FALSE"))
    

    user = relationship("User", back_populates="groups")
    repos = relationship("UserRepo", back_populates="group")

    @staticmethod
    def insert(session, user_id:int, group_name:str) -> dict:
        """Add a group to the user.

        Args
            user_id: id of the user
            group_name: name of the group being added

        Returns:
            Dict with status key that indicates the success of the operation

        Note:
            If group already exists the function will return that it has been added, but a duplicate group isn't added.
            It simply detects that it already exists and doesn't add it.
        """

        if not isinstance(user_id, int) or not isinstance(group_name, str):
            return False, {"status": "Invalid input"}

        user_group_data = {
            "name": group_name,
            "user_id": user_id
        }

        user_group = session.query(UserGroup).filter(UserGroup.user_id == user_id, UserGroup.name == group_name).first()
        if user_group:
            return False, {"status": "Group already exists"}

        try:
            result = session.insert_data(user_group_data, UserGroup, ["name", "user_id"], return_columns=["group_id"])
        except IntegrityError:
            return False, {"status": "Error: User id does not exist"}


        if result:
            return True, {"status": "Group created"}


        return False, {"status": "Error while creating group"}

    @staticmethod
    def delete(session, user_id: int, group_name: str) -> dict:
        """ Delete a users group of repos.

        Args:
            user_id: id of the user
            group_name: name of the users group

        Returns:
            Dict with a status key that indicates the result of the operation

        """

        group = session.query(UserGroup).filter(UserGroup.name == group_name, UserGroup.user_id == user_id).first()
        if not group:
                return False, {"status": "WARNING: Trying to delete group that does not exist"}

        # delete rows from user repos with group_id
        for repo in group.repos:
            session.delete(repo)

        # delete group from user groups table
        session.delete(group)

        session.commit()

        return True, {"status": "Group deleted"}

    @staticmethod
    def convert_group_name_to_id(session, user_id: int, group_name: str) -> int:
        """Convert a users group name to the database group id.

        Args:
            user_id: id of the user
            group_name: name of the users group

        Returns:
            None on failure. The group id on success.

        """

        if not isinstance(user_id, int) or not isinstance(group_name, str):
            return None

        try:
            user_group = session.query(UserGroup).filter(UserGroup.user_id == user_id, UserGroup.name == group_name).one()
        except NoResultFound:
            return None

        return user_group.group_id



class UserRepo(Base):
    __tablename__ = "user_repos"
    __table_args__ = { "schema": "augur_operations" }

    group_id = Column(
        ForeignKey("augur_operations.user_groups.group_id", name="user_repo_group_id_fkey"), primary_key=True, nullable=False
    )
    repo_id = Column(
        ForeignKey("augur_data.repo.repo_id", name="user_repo_user_id_fkey"), primary_key=True, nullable=False
    )

    repo = relationship("Repo", back_populates="user_repo")
    group = relationship("UserGroup", back_populates="repos")

    @staticmethod
    def insert(session, repo_id: int, group_id:int = 1) -> bool:
        """Add a repo to a user in the user_repos table.

        Args:
            repo_id: id of repo from repo table
            user_id: id of user_id from users table
        """

        if not isinstance(repo_id, int) or not isinstance(group_id, int):
            return False

        repo_user_group_data = {
            "group_id": group_id,
            "repo_id": repo_id
        }


        repo_user_group_unique = ["group_id", "repo_id"]
        return_columns = ["group_id", "repo_id"]

        try:
            data = session.insert_data(repo_user_group_data, UserRepo, repo_user_group_unique, return_columns)
        except IntegrityError:
            return False

        return data[0]["group_id"] == group_id and data[0]["repo_id"] == repo_id
    
    @staticmethod
    def add_gitlab_repo(session, url: List[str], user_id: int, group_name=None, group_id=None, from_org_list=False, repo_group_id=None) -> dict:
        """Add repo to the user repo table

        Args:
            urls: list of repo urls
            user_id: id of user_id from users table
            group_name: name of group to add repo to.
            group_id: id of the group
            valid_repo: boolean that indicates whether the repo has already been validated

        Note:
            Either the group_name or group_id can be passed not both

        Returns:
            Dict that contains the key "status" and additional useful data
        """

        if group_name and group_id:
            return False, {"status": "Pass only the group name or group id not both"}

        if not group_name and not group_id:
            return False, {"status": "Need group name or group id to add a repo"}

        if group_id is None:

            group_id = UserGroup.convert_group_name_to_id(session, user_id, group_name)
            if group_id is None:
                return False, {"status": "Invalid group name"}

        if not from_org_list:
            result = Repo.is_valid_gitlab_repo(session, url)
            if not result[0]:
                return False, {"status": result[1]["status"], "repo_url": url}

        # if no repo_group_id is passed then assign the repo to the frontend repo group
        if repo_group_id is None:

            frontend_repo_group = session.query(RepoGroup).filter(RepoGroup.rg_name == FRONTEND_REPO_GROUP_NAME).first()
            if not frontend_repo_group:
                return False, {"status": "Could not find repo group with name 'Frontend Repos'", "repo_url": url}

            repo_group_id = frontend_repo_group.repo_group_id


        repo_id = Repo.insert_gitlab_repo(session, url, repo_group_id, "Frontend")
        if not repo_id:
            return False, {"status": "Repo insertion failed", "repo_url": url}

        result = UserRepo.insert(session, repo_id, group_id)
        if not result:
            return False, {"status": "repo_user insertion failed", "repo_url": url}

        #collection_status records are now only added during collection -IM 5/1/23
        #status = CollectionStatus.insert(session, repo_id)
        #if not status:
        #    return False, {"status": "Failed to create status for repo", "repo_url": url}

        return True, {"status": "Repo Added", "repo_url": url}

    @staticmethod
    def add_github_repo(session, url: List[str], user_id: int, group_name=None, group_id=None, from_org_list=False, repo_type=None, repo_group_id=None) -> dict:
        """Add repo to the user repo table

        Args:
            urls: list of repo urls
            user_id: id of user_id from users table
            group_name: name of group to add repo to.
            group_id: id of the group
            valid_repo: boolean that indicates whether the repo has already been validated

        Note:
            Either the group_name or group_id can be passed not both

        Returns:
            Dict that contains the key "status" and additional useful data
        """

        if group_name and group_id:
            return False, {"status": "Pass only the group name or group id not both"}

        if not group_name and not group_id:
            return False, {"status": "Need group name or group id to add a repo"}

        if from_org_list and not repo_type:
            return False, {"status": "Repo type must be passed if the repo is from an organization's list of repos"}

        if group_id is None:

            group_id = UserGroup.convert_group_name_to_id(session, user_id, group_name)
            if group_id is None:
                return False, {"status": "Invalid group name"}

        if not from_org_list:
            result = Repo.is_valid_github_repo(session, url)
            if not result[0]:
                return False, {"status": result[1]["status"], "repo_url": url}

            repo_type = result[1]["repo_type"]

        # if no repo_group_id is passed then assign the repo to the frontend repo group
        if repo_group_id is None:

            frontend_repo_group = session.query(RepoGroup).filter(RepoGroup.rg_name == FRONTEND_REPO_GROUP_NAME).first()
            if not frontend_repo_group:
                return False, {"status": "Could not find repo group with name 'Frontend Repos'", "repo_url": url}

            repo_group_id = frontend_repo_group.repo_group_id


        repo_id = Repo.insert_github_repo(session, url, repo_group_id, "Frontend", repo_type)
        if not repo_id:
            return False, {"status": "Repo insertion failed", "repo_url": url}

        result = UserRepo.insert(session, repo_id, group_id)
        if not result:
            return False, {"status": "repo_user insertion failed", "repo_url": url}

        #collection_status records are now only added during collection -IM 5/1/23
        #status = CollectionStatus.insert(session, repo_id)
        #if not status:
        #    return False, {"status": "Failed to create status for repo", "repo_url": url}

        return True, {"status": "Repo Added", "repo_url": url}

    @staticmethod
    def delete(session, repo_id:int, user_id:int, group_name:str) -> dict:
        """ Remove repo from a users group.

        Args:
            repo_id: id of the repo to remove
            user_id: id of the user
            group_name: name of group the repo is being removed from

        Returns:
            Dict with a key of status that indicates the result of the operation
        """

        if not isinstance(repo_id, int) or not isinstance(user_id, int) or not isinstance(group_name, str):
            return False, {"status": "Invalid types"}

        group_id = UserGroup.convert_group_name_to_id(session, user_id, group_name)
        if group_id is None:
            return False, {"status": "Invalid group name"}

                # delete rows from user repos with group_id
        session.query(UserRepo).filter(UserRepo.group_id == group_id, UserRepo.repo_id == repo_id).delete()
        session.commit()

        return True, {"status": "Repo Removed"}

    @staticmethod
    def add_github_org_repos(session, url: List[str], user_id: int, group_name: int):
        """Add list of orgs and their repos to a users repos.

        Args:
            urls: list of org urls
            user_id: id of user_id from users table
        """

        group_id = UserGroup.convert_group_name_to_id(session, user_id, group_name)
        if group_id is None:
            return False, {"status": "Invalid group name"}

        # parse github owner url to get owner name
        owner = Repo.parse_github_org_url(url)
        if not owner:
            return False, {"status": "Invalid owner url"}

        result = retrieve_owner_repos(session, owner)

        # if the result is returns None or []
        if not result[0]:
            return False, result[1]

        repos = result[0]
        type = result[1]["owner_type"]

        # get repo group if it exists
        try:
            repo_group = RepoGroup.get_by_name(session, owner)
        except MultipleResultsFound:
            print("Error: Multiple Repo Groups with the same name found with name: {}".format(owner))

            return False, {"status": "Multiple Repo Groups with the same name found"}

        # if it doesn't exist create one
        if not repo_group:
            repo_group = RepoGroup(rg_name=owner.lower(), rg_description="", rg_website="", rg_recache=0, rg_type="Unknown",
                    tool_source="Loaded by user", tool_version="1.0", data_source="Git")
            session.add(repo_group)
            session.commit()

        repo_group_id = repo_group.repo_group_id


        # try to get the repo group with this org name
        # if it does not exist create one
        failed_repos = []
        for repo in repos:

            result = UserRepo.add_github_repo(session, repo, user_id, group_id=group_id, from_org_list=True, repo_type=type, repo_group_id=repo_group_id)

            # keep track of all the repos that failed
            if not result[0]:
                failed_repos.append(repo)

        # Update repo group id to new org's repo group id if the repo
        # is a part of the org and existed before org added
        update_stmt = (
            update(Repo)
            .where(Repo.repo_path == f"github.com/{owner}/")
            .where(Repo.repo_group_id != repo_group_id)
            .values(repo_group_id=repo_group_id)
        )
        session.execute(update_stmt)
        session.commit()

        failed_count = len(failed_repos)
        if failed_count > 0:
            # this should never happen because an org should never return invalid repos
            return False, {"status": f"{failed_count} repos failed", "repo_urls": failed_repos, "org_url": url}

        return True, {"status": "Org repos added"}

class UserSessionToken(Base):
    __tablename__ = "user_session_tokens"
    __table_args__ = { "schema": "augur_operations" }

    token = Column(String, primary_key=True, nullable=False)
    user_id = Column(ForeignKey("augur_operations.users.user_id", name="user_session_token_user_id_fkey"), nullable=False)
    expiration = Column(BigInteger)
    application_id = Column(ForeignKey("augur_operations.client_applications.id", name="user_session_token_application_id_fkey"))
    created_at = Column(BigInteger)

    user = relationship("User", back_populates="tokens")
    application = relationship("ClientApplication", back_populates="sessions")
    refresh_tokens = relationship("RefreshToken", back_populates="user_session")

    @staticmethod
    def create(session, user_id, application_id, seconds_to_expire=86400):
        import time

        user_session_token = secrets.token_hex()
        expiration = int(time.time()) + seconds_to_expire

        user_session = UserSessionToken(token=user_session_token, user_id=user_id, application_id = application_id, expiration=expiration)

        session.add(user_session)
        session.commit()

        return user_session

    def delete_refresh_tokens(self, session):

        refresh_tokens = self.refresh_tokens
        for token in refresh_tokens:
            session.delete(token)
        session.commit()

        session.delete(self)
        session.commit()

class ClientApplication(Base):
    __tablename__ = "client_applications"
    __table_args__ = { "schema": "augur_operations" }

    id = Column(String, primary_key=True, nullable=False)
    user_id = Column(ForeignKey("augur_operations.users.user_id", name="client_application_user_id_fkey"), nullable=False)
    name = Column(String, nullable=False)
    redirect_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)

    user = relationship("User", back_populates="applications")
    sessions = relationship("UserSessionToken")
    subscriptions = relationship("Subscription", back_populates="application")

    def __eq__(self, other):
        return isinstance(other, ClientApplication) and str(self.id) == str(other.id)

    @staticmethod
    def get_by_id(session, client_id):

        try:
            return session.query(ClientApplication).filter(ClientApplication.id == client_id).first()
        except Exception as e:
            session.rollback()
            raise e


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = { "schema": "augur_operations" }

    application_id = Column(ForeignKey("augur_operations.client_applications.id", name="subscriptions_application_id_fkey"), primary_key=True)
    type_id = Column(ForeignKey("augur_operations.subscription_types.id", name="subscriptions_type_id_fkey"), primary_key=True)

    application = relationship("ClientApplication", back_populates="subscriptions")
    type = relationship("SubscriptionType", back_populates="subscriptions")

class SubscriptionType(Base):
    __tablename__ = "subscription_types"
    __table_args__ = (
        UniqueConstraint('name', name='subscription_type_title_unique'),
        {"schema": "augur_operations"}
    )


    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)

    subscriptions = relationship("Subscription", back_populates="type")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint('user_session_token', name='refresh_token_user_session_token_id_unique'),
        {"schema": "augur_operations"}
    )

    id = Column(String, primary_key=True)
    user_session_token = Column(ForeignKey("augur_operations.user_session_tokens.token", name="refresh_token_session_token_id_fkey"), nullable=False)

    user_session = relationship("UserSessionToken", back_populates="refresh_tokens")

    @staticmethod
    def create(session, user_session_token_id):

        refresh_token_id = secrets.token_hex()

        refresh_token = RefreshToken(id=refresh_token_id, user_session_token=user_session_token_id)

        session.add(refresh_token)
        session.commit()

        return refresh_token


class CollectionStatus(Base):
    __tablename__ = "collection_status"
    __table_args__ = (

        #TODO: normalize this table to have a record per repo and collection hook instead of just being per repo.

        #Constraint to prevent nonsensical relationship states between core_data_last_collected and core_status
        #Disallow core_data_last_collected status to not be set when the core_status column indicates data has been collected
        #Disallow core_data_last_collected status to be set when the core_status column indicates data has not been collected
        CheckConstraint(
            "NOT (core_data_last_collected IS NULL AND core_status = 'Success') AND "
            "NOT (core_data_last_collected IS NOT NULL AND core_status = 'Pending')",
            name='core_data_last_collected_check'
        ),

        #Constraint to prevent nonsensical relationship states between core_task_id and core_status
        #Disallow state where core_task_id is set but core_status indicates repo is not running
        #Disallow state where core_task_id is not set but core_status indicates repo is running.
        CheckConstraint(
            "NOT (core_task_id IS NOT NULL AND core_status IN ('Pending', 'Success', 'Error')) AND "
            "NOT (core_task_id IS NULL AND core_status = 'Collecting')",
            name='core_task_id_check'
        ),

        #Constraint to prevent nonsensical relationship states between secondary_data_last_collected and secondary_status
        #Disallow secondary_data_last_collected to not be set when secondary_status indicates task has succeeded
        #Disallow secondary_data_last_collected to be set when secondary_status indicates task hasn't started
        CheckConstraint(
            "NOT (secondary_data_last_collected IS NULL AND secondary_status = 'Success') AND "
            "NOT (secondary_data_last_collected IS NOT NULL AND secondary_status = 'Pending')",
            name='secondary_data_last_collected_check'
        ),

        #Constraint to prevent nonsensical relationship states between secondary_task_id and secondary_status
        #Disallow secondary_task_id to be set when secondary status indicates that task is not running
        #Disallow secondary_task_id to not be set when secondary status indicates that task is running
        CheckConstraint(
            "NOT (secondary_task_id IS NOT NULL AND secondary_status IN ('Pending', 'Success', 'Error')) AND "
            "NOT (secondary_task_id IS NULL AND secondary_status = 'Collecting')",
            name='secondary_task_id_check'
        ),

        #Constraint to prevent nonsensical relationship between facade_data_last_collected
        #Disallow facade_data_last_collected to not be set when facade_status indicates task has been run
        #Disallow facade_data_last_collected to be set when facade_status indicates task hasn't been run
        CheckConstraint(
            "NOT (facade_data_last_collected IS NULL AND facade_status  = 'Success' ) AND"
            "NOT (facade_data_last_collected IS NOT NULL AND facade_status IN ('Pending','Initializing', 'Update'))",
            name='facade_data_last_collected_check'
        ),

        #Constraint to prevent nonsensical relationship between facade_task_id and facade_status
        #Disallow facade_task_id to be set when facade_status indicates task isn't running
        #Disallow facade_task_id to not be set when facade_status indicates task is running
        CheckConstraint(
            "NOT (facade_task_id IS NOT NULL AND facade_status IN ('Pending', 'Success', 'Error', 'Failed Clone')) AND "
            "NOT (facade_task_id IS NULL AND facade_status IN ('Collecting'))",
            name='facade_task_id_check'
        ),

        #Disallow core_status to show core_status hasn't been run while secondary_status is running.
        CheckConstraint(
            "NOT (core_status = 'Pending' AND secondary_status = 'Collecting')",
            name='core_secondary_dependency_check'
        ),
        {"schema": "augur_operations"}
    )

    repo_id = Column(ForeignKey("augur_data.repo.repo_id", name="collection_status_repo_id_fk"), primary_key=True)
    core_data_last_collected = Column(TIMESTAMP)
    core_status = Column(String, nullable=False, server_default=text("'Pending'"))
    core_task_id = Column(String)
    secondary_status = Column(String, nullable=False, server_default=text("'Pending'"))
    secondary_data_last_collected = Column(TIMESTAMP)
    secondary_task_id = Column(String)
    event_last_collected = Column(TIMESTAMP)

    facade_status = Column(String,nullable=False, server_default=text("'Pending'"))
    facade_data_last_collected = Column(TIMESTAMP)
    facade_task_id = Column(String)

    ml_status = Column(String,nullable=False, server_default=text("'Pending'"))
    ml_data_last_collected = Column(TIMESTAMP)
    ml_task_id = Column(String)

    core_weight = Column(BigInteger)
    facade_weight = Column(BigInteger)
    secondary_weight = Column(BigInteger)
    ml_weight = Column(BigInteger)

    issue_pr_sum = Column(BigInteger)
    commit_sum = Column(BigInteger)

    repo = relationship("Repo", back_populates="collection_status")

    @staticmethod
    def insert(session, logger, repo_id):
        from augur.tasks.github.util.util import get_repo_weight_by_issue
        from augur.tasks.util.worker_util import calculate_date_weight_from_timestamps

        repo = Repo.get_by_id(session, repo_id)
        repo_git = repo.repo_git

        collection_status_unique = ["repo_id"]
        pr_issue_count = 0
        github_weight = 0
        if "github" in repo_git:

            try:
                pr_issue_count = get_repo_weight_by_issue(logger, repo_git)
                #session.logger.info(f"date weight: {calculate_date_weight_from_timestamps(repo.repo_added, None)}")
                github_weight = pr_issue_count - calculate_date_weight_from_timestamps(repo.repo_added, None)
            except Exception as e:
                pr_issue_count = None
                github_weight = None
                logger.error(
                        ''.join(traceback.format_exception(None, e, e.__traceback__)))
        else:   
            try:
                pr_issue_count = 0
                github_weight = pr_issue_count - calculate_date_weight_from_timestamps(repo.repo_added, None)
            except Exception as e:
                pr_issue_count = None
                github_weight = None
                logger.error(
                        ''.join(traceback.format_exception(None, e, e.__traceback__)))


        record = {
            "repo_id": repo_id,
            "issue_pr_sum": pr_issue_count,
            "core_weight": github_weight,
            "secondary_weight": github_weight,
            "ml_weight": github_weight
        }
     

        result = session.insert_data(record, CollectionStatus, collection_status_unique, on_conflict_update=False)

        logger.info(f"Trying to insert repo \n issue and pr sum: {record['issue_pr_sum']}")

        if not result:
            return False

        return True
