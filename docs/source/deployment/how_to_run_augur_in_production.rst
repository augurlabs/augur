Running Augur in Production
===========================

This page collects practical tips, configuration notes, and important considerations
for deploying Augur in a production environment. This is a reference to help
configure Augur effectively.

Environment Variables
---------------------

Augur uses several environment variables in production. Make sure to configure the ones relevant
to your deployment:

- ``AUGUR_RESET_LOGS`` : Controls automatic log reset on server startup
- ``AUGUR_DB`` : PostgreSQL database connection string (used if variable not set)

AUGUR_RESET_LOGS
----------------

**Description:**  
Controls whether Augur resets its log files every time the server starts. Useful for managing log size or integrating with external log rotation systems.

**Type:**  
boolean

**Default:**  
`True` : Augur clears old logs at startup.

**Environment Variable:**  
AUGUR_RESET_LOGS

**Notes:**  
If set to `False`, Augur will not reset logs automatically. Administrators must ensure log rotation or cleanup is handled manually.

**Usage Example:**

.. code-block:: bash

   export AUGUR_RESET_LOGS=False

AUGUR_DB
--------

**Description:**  
Specifies the connection string for the PostgreSQL database used by Augur. If omitted, the default Docker database is used.

**Type:**  
string

**Default:**  
Docker container database (if `AUGUR_DB` is not specified)

**Environment Variable:**  
AUGUR_DB

Related Resources
-----------------

- https://github.com/oss-aspen/infra-ansible/
- https://github.com/chaoss/augur-utilities/