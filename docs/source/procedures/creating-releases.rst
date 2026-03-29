The Augur Release Process
=========================

The first step to releasing any changes is to have changes in the first place.
Augur's `CONTRIBUTING.md <https://github.com/chaoss/augur/blob/main/CONTRIBUTING.md>`__ file
contains all the information that is needed to get started with topics like
reporting issues, contributing code, and understanding the code review process.

This document outlines how these changes end up in an Augur release after they are merged into the `main` branch.

Release Workflow
----------------

Starting after version **0.89.3**, Augur follows a workflow similar to those you may already
be familiar with (such as GitHub Flow and Git Flow). The Augur workflow has two long-lived branches,
`main` and `release`, and is designed such that changes only flow in one direction — from `main` into `release`.

Branches
--------

**main**

The `main` branch is the primary development branch that is the target for all new pull requests.
At any given point in time, this branch represents the best approximation of what the next upcoming
release will look like. Since this is the active development branch, changes happen more frequently
and this branch should be considered to be less stable than the `release` branch due to the possibility
of breaking changes being made (and potentially reverted) between releases. It is not recommended for
production deployment and is primarily intended for use by Augur contributors running their own copies
against test data for development purposes.

**release**

The `release` branch is where all Augur versions (after 0.89.3) are tagged. Each commit on this branch
represents either a hotfix to the prior release or a new major or minor version.

Currently, Augur only officially supports the last-released version represented by the latest **release** tag.
In most cases, the latest commit on the `release` branch is made immediately prior to a release, but always rely
on the latest tagged release, not the `release` branch in production.

.. note::

    If future needs require supporting multiple Augur versions concurrently, individual numbered
    release branches may be made from this central `release` branch to allow any hotfixes to be applied
    to each supported version independently of the others.


The Release Process
-------------------

When the next release is set to be cut, some preparation steps need to take place first. These include:

- Ensuring all features planned for that release are merged, and any unrelated changes are delayed (as appropriate) until after the release.
- Creating a Pull Request to update any applicable metadata (such as version information and changelogs) on the `main` branch.

Version Management (Updated)
----------------------------

Starting from version **0.90.0**, Augur now uses a **single source of truth** for its version information,
defined in `metadata.py`.

Previously, the version number needed to be manually updated in several different places during a release, including:

- ``pyproject.toml`` (for Python packaging)
- Dockerfiles (used for building and tagging images)
- GitHub Actions workflow files (e.g., ``.github/workflows/build_docker.yml``)
- Any scripts or documentation pages referencing specific versions

This manual process increased the chance of version mismatches between code, Docker images, and releases.

Now, this has been **fully centralized**:

- The version number is declared once in ``metadata.py`` as ``__version__``.
- A helper script ``get_version.py`` reads this value and dynamically injects it into Docker builds via a build argument.
- The CI/CD pipeline (GitHub Actions) also reads the same version from ``metadata.py`` when tagging builds and Docker images.

This ensures that all parts of Augur — including Python packaging, Docker images, and release artifacts —
use the **exact same version**, automatically.

Therefore, before tagging a new release, only the version in ``metadata.py`` needs to be updated.
All other build and deployment steps automatically consume this version during the release process.

Once all release preparation has been completed, a new Pull Request can be created to merge the `main`
branch into the `release` branch. This creates a final review opportunity and allows for another run of
(potentially more stringent) CI jobs compared to those run on `main`, catching issues that may have come up
throughout the various merges or during the process of preparing for release.

After this PR is merged, a tag is created that points to the commit on the `release` branch,
effectively labeling it so that it can be returned to later if needed. This labeling process can
also be the basis for additional CI jobs that build and upload the released code to distribution
platforms such as Docker Hub or the GitHub Container Registry.


Why?
----

This is done to solve a number of problems:

- Having changes moving in two directions at once (i.e. features coming from `main`, and hotfixes coming from `release`)
  was often confusing and increased the odds that a change would be missed, such as being shipped as a hotfix
  but not merged into the main codebase — leading to a regression in the next release.


Special Case: Hotfixes
----------------------

If the fix is a hotfix:

- Changelog updates and other metadata changes should be included as part of the PR.
- This is where tools like **Mergeify** can help re-create the PR targeting the `release` branch directly,
  at which point the regular release process is followed.
