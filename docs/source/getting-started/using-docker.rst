Docker Compose
==============
For quickest start up, set up Docker or Podman desktop with a machine with roughly
the following resources (or more).

- 8 CPUs
- 100 GB disk
- 10 GB RAM

1. Clone the Augur repository https://github.com/chaoss/augur


2. Create a ``.env`` file in the top level directory with the following fields (don't remove any variable, keep placeholder values if you don't need some of them):

.. code:: python

    AUGUR_DB=augur
    AUGUR_DB_USER=augur
    AUGUR_DB_PASSWORD=password_here

    AUGUR_GITHUB_API_KEY=ghp_value_here
    AUGUR_GITHUB_USERNAME=gh_username
    AUGUR_GITLAB_API_KEY=placeholder
    AUGUR_GITLAB_USERNAME=placeholder

3. Build the container using one of the following commands:

.. code:: shell

    docker compose up --build

or

.. code:: shell

    podman compose up --build

And augur should be up and running! Over time, you may decide that you want to download and run newer releases of Augur. It is critical that your ``.env`` file remains configured to use the same database name and password; though you can change the password if you understand how to connect to a database running inside a Docker container on your computer.

Rebuilding Augur in Docker
----------------------------
We do not recommend running the augur database in a Docker container in production, though for light installations (~ < 2,000 repos) it is OK as long as you understand that your data exists inside of a Docker container, and you will **need to back that up** if you want to avoid data loss.

You can identify the physical location of your Docker database file system using these commands:

.. code:: shell

    docker volume ls
    docker volume inspect <volume_name>

For example:

.. code:: shell

    ➜  augur-demo git:(docker-docs-patch-12) ✗ docker volume inspect augur-demo_augurpostgres
    [
        {
            "CreatedAt": "2025-06-25T16:19:20Z",
            "Driver": "local",
            "Labels": {
                "com.docker.compose.config-hash": "5aae21cec561d5da3e9a0b92ccab7470394b21cf473803bd85055c4589535355",
                "com.docker.compose.project": "augur-demo",
                "com.docker.compose.version": "2.37.1",
                "com.docker.compose.volume": "augurpostgres"
            },
            "Mountpoint": "/var/lib/docker/volumes/augur-demo_augurpostgres/_data",
            "Name": "augur-demo_augurpostgres",
            "Options": null,
            "Scope": "local"
        }
    ]

To rebuild a fresh Augur database in Docker, follow these steps:

1. **Stop the running containers** (if any):

    .. code:: shell

        docker compose down

2. **Remove the existing database volumes and containers** to clear all data:

    .. code:: shell

        docker system prune -af
        docker volume prune -af

3. **Rebuild and start the containers**:

    .. code:: shell

        docker compose up --build
