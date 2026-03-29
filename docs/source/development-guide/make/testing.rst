Testing
=======

**THIS SECTION IS UNDER CONSTRUCTION.**

If you have questions or would like to help please open an issue on GitHub_.

.. _GitHub: https://github.com/chaoss/augur/issues

These commands are used to run specific subsets of unit tests. We use ``pytest`` as our test runner.

--------------

``make test``
-------------
This command runs ALL available tests for both the metric functions and their API endpoints.

Example\:

.. code-block:: bash

  $ make test

--------------

``make test-metrics``
------------------------
This command will run ALL unit tests for the metric functions.

Example\:

.. code-block:: bash

  $ make test-metrics

--------------

``make test-metrics-api``
--------------------------
The above command runs ALL tests for the metrics API.

Example\:

.. code-block:: bash

  $ make test-metrics-api

--------------

``pytest``
----------
You can also run the tests directly using the ``pytest`` command.

Example\:

.. code-block:: bash

  $ uv run pytest
