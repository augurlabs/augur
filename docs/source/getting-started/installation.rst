Installation Guide
===================

This section shows how to install Augur's Python library from the source. If you don't have a required dependency, please follow the provided links to install and configure it.

.. note::

  There are three main issues new developers encounter when first installing Augur:

  1. The absence of a `GCC` or `Fortran` compiler; which are required by NumPy and NLTK Python libraries. Look up how to install these compilers for your local operating system. Many times they need to be updated to a more current version.

  2. Conflicting versions of Python: The fix is platform-specific. On Mac OS X, multiple versions of Python often have been installed by the OS, brew, Anaconda, or both. The result is some python commands draw from different paths because of how they link in `/usr/local/bin`

  3. Multiple, or conflicting versions of PostgreSQL, sometimes due to the absence of a functional `psql` function at the command line.

General Requirements
~~~~~~~~~~~~~~~~~~~~

Backend
---------
Required:

-  `GitHub Access Token <https://github.com/settings/tokens>`_ (This token
   only needs to have sufficient privileges to read the repos you want to
   collect. Assuming those are all "public" repositories, this token can be a
   `"no scope" token
   <https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps#available-scopes>`_,
   i.e., leave all scopes UNchecked.)
-  `GitLab Access Token <https://gitlab.com/profile/personal_access_tokens>`__
-  `Python 3.6 - 3.8 <https://www.python.org/downloads/>`__



Our REST API & data collection workers query the GitHub & GitLab API to collect data about issues, pull requests, contributors, and other information about a repository. Values for GitLab and GitHub access tokens are **required** for data collection and must be provided (an invalid token can be provided if you don't plan to use one platform) .

Optional:

-  `Go 1.12 or later <https://golang.org/doc/install>`__

The ``value_worker`` uses a Go package called `scc <https://github.com/boyter/scc>`_ to run COCOMO calculations.
Once you've installed Go, follow the appropriate steps for your system to install the ``scc`` package.

-  Install gcc OpenMP Support: ``sudo apt-get install libgomp1`` -- Ubuntu

The ``message_insights_worker`` uses a system-level package called OpenMP. You will need this installed at the system level for that worker to work.

Caching System (Redis)
----------------------
* `Linux Installation <https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/install-redis-on-linux/>`__
* `Mac Installation <https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/install-redis-on-mac-os/>`__
* `Windows Installation <https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/install-redis-on-windows/>`__

Message Broker (RabbitMQ)
-------------------------
* `Linux Installation <https://www.rabbitmq.com/download.html>`__
* `Mac Installation <https://www.rabbitmq.com/install-homebrew.html>`__
* `Windows Installation <https://www.rabbitmq.com/install-windows.html>`__

After installation, you must also set up your rabbitmq instance by running the below commands:

.. code-block:: bash

	sudo rabbitmqctl add_user augur password123

	sudo rabbitmqctl add_vhost augur_vhost

	sudo rabbitmqctl set_user_tags augur augurTag

	sudo rabbitmqctl set_permissions -p augur_vhost augur ".*" ".*" ".*"

.. note::
	it is important to have a static hostname when using rabbitmq as it uses hostname
	to communicate with nodes.

Then, start rabbitmq server with

.. code-block:: bash

    sudo systemctl start rabbitmq.service


If your setup of rabbitmq is successful your broker url should look like this:

``broker_url = 'amqp://augur:password123@localhost:5672/augur_vhost'``

During installation you will be prompted for this broker url.

Frontend
---------
If you're interested in using our visualizations, you can optionally install the frontend dependencies:

-  `Node <https://nodejs.org/en/>`__
-  `npm <https://www.npmjs.com/>`__
-  `Vue.js <https://vuejs.org/>`__
-  `Vue-CLI <https://cli.vuejs.org/>`__

We use Vue.js as our frontend web framework and ``npm`` as our package manager.


Visualization API calls
---------------------------

On Ubuntu and other Linux flavors: if you want to use the new Augur API Calls that generate downloadable graphics developed in the `https://github.com/chaoss/augur-community-reports` repository, you need to install the `firefox-geckodriver` (on Ubuntu or Red Hat Fedora) or `geckodriver` on Mac OSX, at the system level. This dependency exists because the Bokeh libraries we use for these APIs require a web browser engine.

For Ubuntu you can use:

.. code-block:: bash

    - which firefox-geckodriver
    - if nothing returned, then:
    - sudo apt install firefox-geckodriver

For Fedora you can use

.. code-block:: bash

    - which firefox-geckodriver
    - if nothing returned, then:
    - sudo dnf install firefox-geckodriver

For Mac OSX you can use:

.. code-block:: bash

    -  which geckodriver
    -  if nothing returned, then:
    -  brew install geckodriver

.. note::
  If you have BOTH Firefox-geckodriver AND ChromeDriver installed the visualization API will not work.

  We have fully tested with Firefox-gecko driver on Linux platforms, and geckodriver on OSX. If you have ONLY ChromeDriver installed, it will probably work. Open an issue if you have a functioning ChromeDriver implementation.


===================
Installation
===================

Now you're ready to build! The steps below outline how to create a virtual environment (**required**) and start the installation process, after which you'll move on to the next section to configure the workers. The instructions are written in a way that you can follow for your respective Operating System.


.. note::
  Lines that start with a ``$`` denote a command that needs to run in an interactive terminal.

.. warning::
  Do **NOT** install or run Augur using ``sudo``. It is not required, and using it will inevitably cause some permissions trouble.

For macOS Errata
~~~~~~~~~~~~~~~~

If you’re running Augur on macOS, we strongly suggest updating your shell’s initialization script in the following:

In a terminal, open the script:

  nano .bash_profile

Add the following line to the end of the file:

  export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

Save the file and exit.
Run this command to reload bash_profile:

  source .bash_profile

Check if it is updated:

  env

``env`` should contain ``OBJC_DISABLE_INITIALIZE_FORK_SAFETY``.

macOS takes "helpful" measures to prevent Python subprocesses (which Augur uses) from forking cleanly, and setting this environment variable disables these safety measures to restore regular Python functionality.

.. warning::
  If you skip this step, you'll likely see all housekeeper jobs randomly exiting for no reason, and the Gunicorn server will not behave nicely either. Skip this step at your own risk!


General Augur Installation Steps (Irrespective of Operating System)
-------------------------------------------------------------------

1. Clone the repository and change to the newly-created directory.

.. code-block:: bash

   $ git clone 'https://github.com/chaoss/augur.git'
   $ cd augur/

2. Install ``uv`` via pip:

.. code:: shell

   pip install --user uv


3. Set AUGUR_DB environment variable with a postgres database connection string (if you have not setup a database yet, refer to :ref:`database setup<Creating a Database>`) Note: Three terminals will be needed to collect data for augur, and AUGUR_DB needs to be set for 2 out of the 3. If you don't want to add it to both terminals you can add it permanently in your .bashrc file if running bash, or .zshrc file if in running zsh.

.. code-block:: bash

    # set postgres database connection string to AUGUR_DB environment variable
    # replace <> variables with actual values
    $ export AUGUR_DB=postgresql+psycopg2://<user>:<password>@<host>:<port>/<database_name>

4. Run the install script. This script will:

- Install Augur’s Python library and application server
- Install Augur's schema in the configured database
- Prompt you for GitHub and GitLab keys
- Add GitHub and GitLab keys to config table in the database

.. note::

  The install script will also generate an Augur API key for your database at the very end. This key will be automatically inserted into your database and printed to your terminal. It requires to use the repo & repo group creation endpoints, so **make sure you save it off somewhere!** There is only one key per database.

.. code-block:: bash

   # run the install script
   $ make install

If you think something went wrong, check the log files in ``logs/``. If you want to try again, you can use ``make clean`` to delete any build files before running ``make install`` again.

MacOS users:
------------

If your build fails and in gunicorn.log you see this error: ``Connection in use: ('0.0.0.0', 5000)``, that means port 5000 is being used by another process. To solve this issue, go to System Preferences -> Sharing -> Disable Airplay Receiver.

If you want to test new code you have written, you can rebuild Augur using:

.. code-block:: bash

   $ make rebuild-dev

.. note::

  If you chose to install Augur's frontend dependencies, you might see a bunch of ``canvas@1.6.x`` and ``canvas-prebuilt@1.6.x`` errors in the installation logs. These are harmless and caused by a few of our dependencies having *optional* requirements for old versions of these libraries. If they seem to be causing you trouble, feel free to open an `issue <https://github.com/chaoss/augur/issues>`_.

To enable log parsing for errors, you need to install `Elasticsearch <https://www.elastic.co/downloads/elasticsearch>`_ and `Logstash <https://www.elastic.co/downloads/past-releases/logstash-6-8-10>`_.

.. warning::

   Please note, that Logstash v7.0 and above have unresolved issues that affect this functionality.

   In order to use it in the near future, please download v6.8.

   If you use a package manager, it defaults to v7+, so we recommend downloading `binary <https://www.elastic.co/downloads/past-releases/logstash-6-8-10>`_ .

   This change is tested with Elasticsearch v7.8.0_2 and Logstash v6.8.10.

Once everything installs, you're ready to `configure your data collection workers <collecting-data.html>`_!
