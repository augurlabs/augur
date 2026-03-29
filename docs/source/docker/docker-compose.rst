Docker Compose Deployment
=========================

This section assumes you have read and configured your Docker installation as detailed `here <toc.html#getting-started>`_.

The default ports for each service are\:

- ``backend``: ``5000:50100-50800``
- ``frontend``: ``8080``
- ``database``: ``5434``

.. note::

    Make sure your database is configured to listen to all addresses to work with the containers. The most common error an improperly configured database throws are
    ::

        psql: could not connect to server: Connection refused
        Is the server running on host 10.254.254.254 and accepting
        TCP/IP connections on port 5432?


Docker Compose
===============================

This section of the documentation details how to use Augur's Docker Compose configuration to get the full stack up and running.

.. warning::

    Don't forget to provide your external database credentials in a file called ``.env`` file. Make sure all the following environment variables are specified, keep placeholder values if you don't need some of them.
    Don't specify AUGUR_DB if you want the docker database to be used.

    Example .env:
    .. code::

        AUGUR_GITHUB_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx
        AUGUR_GITHUB_USERNAME=usernameGithub
        AUGUR_GITLAB_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx
        AUGUR_GITLAB_USERNAME=usernameGitlab
        AUGUR_DB=yourDBString



To run Augur **without** the database container:

.. code-block:: bash

    docker compose -f docker-compose.yml up

To run Augur **with** the database container:

.. code-block:: bash

    docker compose -f docker-compose.yml -f database-compose.yml up


Stopping the containers
-------------------------

To stop the containers, run ``docker compose down --remove-orphans``. The flag is necessary to stop the database container if you used one; run the command again to delete them.

Once you've got your container up and running, checkout out `how to use them <usage.html>`_
