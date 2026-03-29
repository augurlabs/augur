Explanations of Technologies
============================

What does Redis Do?
^^^^^^^^^^^^^^^^^^^

Redis is used to make the state of data collection jobs visible on an
external dashboard, like Flower. Internally, Augur relies on Redis to
cache GitHub API Keys, and for OAuth Authentication. Redis is used to
maintain awareness of Augur’s internal state.

What does RabbitMQ Do?
^^^^^^^^^^^^^^^^^^^^^^

Augur is a distributed system. Even on one server, there are many
collection processes happening simultaneously. Each job to collect data
is put on the RabbitMQ Queue by Augur’s “Main Brain”. Then independent
workers pop messages off the RabbitMQ Queue and go collect the data.
These tasks then become standalone processes that report their
completion or failure states back to the Redis server.

**Edit** the ``/etc/redis/redis.conf`` file to ensure these parameters
are configured in this way:

.. code:: shell

   supervised systemd
   databases 900
   maxmemory-samples 10
   maxmemory 20GB

**NOTE**: You may be able to have fewer databases and lower maxmemory
settings. This is a function of how many repositories you are collecting
data for at a given time. The more repositories you are managing data
for, the close to these settings you will need to be.

**Consequences** : If the settings are too low for Redis, Augur’s
maintainer team has observed cases where collection appears to stall.
(TEAM: This is a working theory as of 3/10/2023 for Ubuntu 22.x, based
on EC2 experiments.)

Possible EC2 Configuration Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With virtualization there may be issues associated with redis-server
connections exceeding available memory. In these cases, the following
workarounds help to resolve issues.

Specifically, you may find this error in your augur logs:

.. code:: shell

   redis.exceptions.ConnectionError: Error 111 connecting to 127.0.0.1:6379. Connection refused.

**INSTALL** ``sudo apt install libhugetlbfs-bin``

**COMMAND**:

::

   hugeadm --thp-never` &&
   echo never > /sys/kernel/mm/transparent_hugepage/enabled

.. code:: shell

   sudo vi /etc/rc.local

**paste** into ``/etc/rc.local``

.. code:: shell

   if test -f /sys/kernel/mm/transparent_hugepage/enabled; then
      echo never > /sys/kernel/mm/transparent_hugepage/enabled
   fi

**EDIT** : ``/etc/default/grub`` add the following line:

.. code:: shell

   GRUB_DISABLE_OS_PROBER=true

Postgresql Configuration
------------------------

Your postgresql instance should optimally allow 1,000 connections:

.. code:: shell

   max_connections = 1000                  # (change requires restart)
   shared_buffers = 8GB                    # min 128kB
   work_mem = 2GB                  # min 64kB

Augur will generally hold up to 150 simultaneous connections while
collecting data. The 1,000 number is recommended to accommodate both
collection and analysis on the same database. Use of PGBouncer or other
utility may change these characteristics.

Augur Commands
--------------

To access command line options, use ``augur --help``. To load repos from
GitHub organizations prior to collection, or in other ways, the direct
route is ``augur db --help``.

Start a Flower Dashboard, which you can use to monitor progress, and
report any failed processes as issues on the Augur GitHub site. The
error rate for tasks is currently 0.04%, and most errors involve
unhandled platform API timeouts. We continue to identify and add fixes
to handle these errors through additional retries. Starting Flower:
``(nohup celery -A augur.tasks.init.celery_app.celery_app flower --port=8400 --max-tasks=1000000 &)``
NOTE: You can use any open port on your server, and access the dashboard
in a browser with http://servername-or-ip:8400 in the example above
(assuming you have access to that port, and its open on your network.)

Starting your Augur Instance
----------------------------

Start Augur: ``(nohup augur backend start &)``

When data collection is complete you will see only a single task running
in your flower Dashboard.

Accessing Repo Addition and Visualization Front End
---------------------------------------------------

Your Augur instance will now be available at
http://hostname.io:port_number

For example: http://chaoss.tv:5038

Note: Augur will run on port 5000 by default (you probably need to
change that in augur_operations.config for OSX)

Stopping your Augur Instance
----------------------------

You can stop augur with ``augur backend stop``, followed by
``augur backend kill``. We recommend waiting 5 minutes between commands
so Augur can shutdown more gently. There is no issue with data integrity
if you issue them seconds apart, its just that stopping is nicer than
killing.
