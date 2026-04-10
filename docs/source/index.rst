Augur Documentation
==================================

:doc:`Welcome! <getting-started/Welcome>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   getting-started/Welcome
   quick-start
   about-augur/toc
   deployment/toc
   getting-started/toc
   development-guide/toc
   rest-api/api
   docker/toc
   schema/toc
   login
   procedures/toc
   history/index
.. 

..
  deployment/toc
..
  schema/toc

.. image:: development-guide/images/augur-architecture-2.png
  :width: 700
  :alt: Development guide image overview of augur


What is Augur?
~~~~~~~~~~~~~~~~
Augur is a software tool that helps you collect and measure information about `open source <https://opensource.com/resources/what-open-source>`_ software projects. Augur focuses on collecting data from public git-based code hosting platforms ("Forges") such as GitHub and GitLab to produce data about the health and sustainability of software projects based on the relevant CHAOSS metrics.

The main goal of Augur is to understand how healthy and sustainable a project is. Healthy projects are easier to rely on, and they are important because many software organizations or companies depend on open-source software.

How Augur works
---------------

1. Augur looks at the project’s repositories (the place where the project’s code and files live).
2. It collects data about activity that is happening in the project, including issues, comments, code changes, etc.
3. It organizes this data into a standard format called a data model.
4. Then it calculates metrics that tell you about the project’s health.

Example of a metric: Burstiness
-------------------------------
- Burstiness is one of Augur’s metrics.
- It shows periods when a project has a lot of activity in a short time, followed by periods when activity goes back to normal.
- This helps you see a project’s focus, update patterns, and stability.
- In other words, you can tell how often big changes happen and whether the project works in a steady, predictable way.

Augur calculates many other metrics, which you can see in the `full list <https://chaoss.community/metrics/>`_.

Who develops Augur
--------------------

- Augur is developed as part of CHAOSS (Community Health Analytics in Open Source Software).
- Many of Augur’s metrics come directly from the CHAOSS community.
- If you want to get involved, visit the `CHAOSS website <https://chaoss.community>`_.

For the current list of Augur maintainers and contributors, please refer to the
`CONTRIBUTORS.md <https://github.com/chaoss/augur/blob/main/CONTRIBUTORS.md>`_
file.

See it in action
-------------------

- You can check out Augur live on the `CHAOSS instance <https://ai.chaoss.io>`_.
