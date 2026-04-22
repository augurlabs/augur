Augur's Frontend
=================

In modern versions of Augur, the frontend is automatically served when you start the Augur server. Here's how to access it:

1. **Start the Augur server** (if not already running):

   Run ``uv run augur run`` to start the server.

2. **Access the frontend**:
   - The frontend is automatically available at ``http://localhost:5002`` by default
   - You can also access it through the main Augur server at ``http://localhost:5000`` (it will redirect to the frontend)

For production deployment behind a web server like nginx, you can configure your web server to proxy requests to the frontend service running on port 5002.

Augur's frontend source code can be found at ``<root_augur_directory>/frontend/src/``. It uses Vue.js as its primary architecture framework, and Vega/Vega-Lite for its visualizations. It's configured via the ``frontend.config.json`` file in ``<root_augur_directory>/frontend/``.

**THIS SECTION IS UNDER CONSTRUCTION.**

If you have questions or would like to help please open an issue on GitHub_.

.. _GitHub: https://github.com/chaoss/augur/issues
