Getting Started
================

For the Docker Savvy Who Want to Understand How the Sausage is Made:
--------------------------------------------------------------------

Augur provides several Docker images designed to get you started with our software as quickly as possible. They are:

- ``augurlabs/augur:backend``, our backend data collection and metrics API
- ``augurlabs/augur:frontend``, our metrics visualization frontend (Experimental, will be replaced in the future)

.. warning::
   The frontend is very out of date and will likely not work. It is still available, but it is in the process of being replaced with an entirely new frontend so the old frontend is not being actively fixed.

- ``augurlabs/augur:database``, an empty PostgreSQL database with the Augur schema installed

If you're not familiar with Docker, their `starting guide <https://www.docker.com/resources/what-container>`_ is a great resource.

The rest of this section of the documentation assumes you have a working installation of Docker as well as some familiarity with basic Docker concepts and a few basic Docker and Docker,Compose commands.

If you are less familiar with Docker, or experience issues you cannot resolve attempting our "quick start", please follow the instructions in this section, and the next few pages, to set up your environment.

Docker Compose
--------------

For quickest start up, set up Docker or Podman desktop with a machine with roughly
the following resources (or more):

- 8 CPUs
- 100 GB disk
- 10 GB RAM

Clone the Augur repository and create a .env file in the top level directory
with the following fields (don't remove any variable, keep placeholder values if you don't need some of them):

.. code:: python

    AUGUR_DB=augur
    AUGUR_DB_USER=augur
    AUGUR_DB_PASSWORD=password_here

    AUGUR_GITHUB_API_KEY=ghp_value_here
    AUGUR_GITHUB_USERNAME=gh_username
    AUGUR_GITLAB_API_KEY=placeholder
    AUGUR_GITLAB_USERNAME=placeholder

Then run:

.. code:: shell

    docker compose up --build

or

.. code:: shell

    podman compose up --build

And augur should be up and running!

Credentials
------------
If you want to create a DB outside of using Docker/Podman Compose, you'll need to set up a PostgreSQL instance either locally or using a remote host.

.. note::

  Make sure your database is configured to listen to all addresses to work with the containers while running locally. These settings can be edited in your ``postgresql.conf``. Additionally, edit the bottom section of your ``pg_hba.conf`` file with:

.. code-block::

      # TYPE  DATABASE        USER            ADDRESS                 METHOD
      host	all  		all 		0.0.0.0/0 		md5

If you're interested solely in data collection, we recommend using our test data with the Docker Compose script. This will start up the backend and frontend containers simultaneously, well as an optional database container; however, if you are looking to collect data long term, we **strongly suggest setting up a persistent database instance**; you can find instructions for doing so `here <../getting-started/database.html>`_. Remember to save off the credentials for your newly minted database; you'll need them shortly.

If you don't care if your data doesn't get persisted or are doing local development, you can use the database containers we provide.

.. warning::

    There are conflicting opinions on using Docker for a production database.

If you're more interested in doing local development, we recommend using our Docker testing environment image - more on that later.

Configuration File
-------------------

Besides a database instance, you will also need a `GitHub Access Token <https://github.com/settings/tokens>`__ (``repo`` and all ``read`` scopes except ``enterprise``). **This is required for all Docker users**.

First, you'll need to clone the repository. In your terminal, run:

.. code-block:: bash

    $ git clone https://github.com/chaoss/augur.git
    $ cd augur/


Now that you've got your external database credentials (if you are using one) and your access token, we'll need to set environment variables manually.

Your database credentials and other environment variables used at runtime are stored in a file when running manually and are taken from the active bash session when using docker compose.

You can provide your own ``.env`` file to pull from. The file should have the below format and set all the variables to some value.

  .. code::

    AUGUR_GITHUB_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx
    AUGUR_GITHUB_USERNAME=usernameGithub
    AUGUR_GITLAB_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx
    AUGUR_GITLAB_USERNAME=usernameGitlab
    AUGUR_DB=yourDBString


Now that you've created your config file or are ready to generate it yourself, you're ready to `get going <quick-start.html>`_ .
