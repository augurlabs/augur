Docker Quick Start
==================================
Before you get off to such a quick start, go ahead and
  1. Create a fork from augur starting at https://github.com/chaoss/augur
  2. Clone that fork locally
  3. Checkout the appropriate branch to work on (see notes below):

  .. code-block:: python

     git checkout main

  4. Create a .env file in the top level directory with the following fields (don't remove any variable, keep placeholder values if you don't need some of them):

.. code:: python

    AUGUR_DB=augur
    AUGUR_DB_USER=augur
    AUGUR_DB_PASSWORD=password_here

    AUGUR_GITHUB_API_KEY=ghp_value_here
    AUGUR_GITHUB_USERNAME=gh_username
    AUGUR_GITLAB_API_KEY=placeholder
    AUGUR_GITLAB_USERNAME=placeholder

5. Build the container using one of the following commands:

.. code:: shell

    docker compose up --build

or

.. code:: shell

    podman compose up --build

And augur should be up and running!

.. note::

  **Running against an external database**:

  If you want to start running docker against an external database right away:

  1. Follow the instructions to create a database, and database user (if you have just installed Postgresql locally, you may need to follow instructions to allow access to Postgresql from Docker on the next page. tl;dr, there are edits to the Postgresql `pg_hba.conf` and `postgresql.conf` files):

  .. code-block:: postgresql

    CREATE DATABASE augur;
    CREATE USER augur WITH ENCRYPTED PASSWORD 'password';
    GRANT ALL PRIVILEGES ON DATABASE augur TO augur;


  2. Install Docker and docker-compose. If you're not familiar with Docker, their `starting guide <https://www.docker.com/resources/what-container>`_ is a great resource.

  3. Create a file to store all relevant enviroment variables for running docker. Below is an example file. This file should be named ``.env```

  .. code-block::

    AUGUR_DB=augur
    AUGUR_DB_USER=augur
    AUGUR_DB_PASSWORD=password_here

    AUGUR_GITHUB_API_KEY=ghp_value_here
    AUGUR_GITHUB_USERNAME=gh_username
    AUGUR_GITLAB_API_KEY=placeholder
    AUGUR_GITLAB_USERNAME=placeholder

  4. Execute the code from the base directory of the Augur repository:

  .. code-block:: bash

    sudo docker build -t augur-docker -f docker/backend/Dockerfile .
    sudo docker compose up
