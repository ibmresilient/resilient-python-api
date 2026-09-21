.. _release-notes:

=============
Release Notes
=============

This page summarises what changed in each release of the IBM SOAR Python
libraries and what you may need to do when upgrading.

All four packages — ``resilient``, ``resilient-circuits``, ``resilient-lib``,
and ``resilient-sdk`` — are released together and share the same version number.

For the complete history of every change, see the **Change Log** section on
each library's individual page.

.. note::

   **Upgrade recommendation:** always upgrade all four packages together.
   Running mismatched versions is unsupported and may cause unexpected behaviour.

   .. code-block:: bash

      pip install -U resilient resilient-circuits resilient-lib resilient-sdk

----

.. _rn-51.0.9.0:

Version 51.0.9.0
-----------------

*Released October 2026*

This release adds official support for Python 3.13 and 3.14 across all four
libraries, removes the ``pytz`` dependency in ``resilient-lib`` in favour of
the standard library ``zoneinfo`` module, fixes timezone handling in
``resilient-lib``, adds workspace export support to ``resilient-sdk``,
migrates all package metadata to ``pyproject.toml`` (PEP 621), and updates
the ``soarapps-base-docker-image`` to UBI9-minimal with a new UBI10-minimal
opt-in build target.

**Package versions**

+------------------------------+-----------+
| Package                      | Version   |
+==============================+===========+
| resilient                    | 51.0.9.0  |
+------------------------------+-----------+
| resilient-circuits           | 51.0.9.0  |
+------------------------------+-----------+
| resilient-lib                | 51.0.9.0  |
+------------------------------+-----------+
| resilient-sdk                | 51.0.9.0  |
+------------------------------+-----------+
| pytest-resilient-circuits    | 51.0.9.0  |
+------------------------------+-----------+
| resilient-app-config-plugins | 1.1.0     |
+------------------------------+-----------+

**What changed**

*All packages* — Test coverage has been extended to include Python 3.13 and
3.14. This confirms that the libraries are compatible with these newer Python
runtimes. Note that the published ``soarapps-base-docker-image`` container
continues to ship **Python 3.12** by default — this change is a testing
extension only and does not affect the Python version used in production
containers or on App Host. Python 3.12 remains the recommended and supported
runtime for deployed apps.

*All packages* — Package metadata has been migrated from ``setup.cfg`` /
``setup.py`` to ``pyproject.toml`` (PEP 621). This is an internal build
tooling change only; published packages on PyPI are unaffected and the
installation experience is identical.

*resilient-lib* — The ``pytz`` dependency has been replaced with the built-in
``zoneinfo`` module. ``pytz`` is no longer maintained and has been superseded
by ``zoneinfo`` (PEP 615) since Python 3.9. This change removes an external
dependency and aligns timezone handling with the Python standard library.

*resilient-lib* — ``readable_datetime`` now always returns a UTC timestamp
regardless of the server's local timezone. Previously, ``fromtimestamp()`` was
called without a timezone, which produced local-time output on servers not set
to UTC.

*resilient-lib* — The ``timestamp`` Jinja filter now uses
``datetime.timestamp()`` instead of ``calendar.timegm(utctimetuple())``. This
correctly handles offset-aware timezones (e.g. ``CET``) and fixes a
one-hour-off result that was present in previous releases.

*resilient-sdk* — Added ``-ws`` / ``--workspace`` option to the ``extract``
command, allowing workspace objects to be included in the generated
``export.res`` file.

*resilient-sdk* — The ``package`` command now invokes ``python -m build
--sdist`` instead of calling ``setup.py sdist`` directly. This is required
now that ``setup.py`` has been removed from all packages.

*resilient-sdk* — The ``codegen --reload`` log notice has been updated to
reference the current Dockerfile template version (v51.0.8.3).

*pytest-resilient-circuits* — Replaced deprecated ``pkg_resources`` with
``importlib.resources`` for loading test data files. This removes the runtime
dependency on ``setuptools`` and is compatible with Python 3.9+.

*pytest-resilient-circuits* — Fixed invalid escape sequences in ``@resilient_endpoint``
regex strings in ``mocks.py`` (converted to raw strings). These raised
``DeprecationWarning`` in Python 3.6–3.11 and become ``SyntaxWarning`` /
errors in Python 3.12+.

*resilient-app-config-plugins* — Fixed an incorrect ``cachetools`` dependency
marker (``python_version > "3.11"`` corrected to ``>= "3.11"``).

*soarapps-base-docker-image* — The base image has been migrated from
``ubi9-minimal`` with ``microdnf``-installed Python to a tarball-based Python
installation sourced from Artifactory. This decouples the Python version from
what is available in the UBI package repository, enabling precise version
pinning and faster future upgrades. A new **UBI10-minimal** build target has
also been added as an opt-in, supporting Python 3.13 and later.

.. warning::

   **Breaking change for teams that build the base image directly.**

   The ``docker build`` command now requires an additional build argument:

   .. code-block:: bash

      --build-arg ARTIFACTORY_API_TOKEN=<token>

   Builds without this argument will fail immediately with an explicit error.
   The token is used to download the Python tarball from the internal
   Artifactory registry. Refer to the ``Dockerfile`` comments for the full
   build command.

   The ``--build-arg PYTHON_SHORT_VERSION`` argument has been replaced by
   ``--build-arg PYTHON_VERSION``, which now expects a full patch version
   (e.g. ``3.12.14``) rather than a minor version (e.g. ``3.12``). Update
   any custom build scripts accordingly.

**Upgrade notes**

- **Standard app developers:** no action required. The base container image
  and App Host continue to run Python 3.12. The ``pytz`` removal in
  ``resilient-lib`` is handled internally and does not affect the public API
  of any function. The ``pyproject.toml`` migration is transparent to
  consumers.
- **Apps that import ``pytz`` directly:** if your own app code imports
  ``pytz`` directly (rather than through ``resilient-lib``), ``pytz`` will no
  longer be installed as a transitive dependency after upgrading. Add
  ``pytz`` explicitly to your app's ``install_requires`` in ``setup.py``, or
  migrate your code to use ``zoneinfo`` from the standard library:

  .. code-block:: python

     # Before
     from pytz import timezone
     tz = timezone("America/New_York")

     # After (Python 3.9+)
     from zoneinfo import ZoneInfo
     tz = ZoneInfo("America/New_York")

- **Teams building the base image:** see the warning above. Update your build
  scripts to pass ``ARTIFACTORY_API_TOKEN`` and switch
  ``PYTHON_SHORT_VERSION`` to ``PYTHON_VERSION`` with the full patch version.
  To use the new UBI10 build, pass ``--build-arg UBI_VERSION=ubi10-minimal``
  and set ``PYTHON_VERSION`` to a 3.13+ patch version (e.g. ``3.13.15``).

----

.. _rn-51.0.8.3:

Version 51.0.8.3
-----------------

*Released July 2026*

This is a dependency maintenance release. No API or behavioural changes were
made to any library. Upgrading is straightforward — no code changes are
required in your apps.

**Package versions**

+---------------------+-----------+
| Package             | Version   |
+=====================+===========+
| resilient           | 51.0.8.3  |
+---------------------+-----------+
| resilient-circuits  | 51.0.8.3  |
+---------------------+-----------+
| resilient-lib       | 51.0.8.3  |
+---------------------+-----------+
| resilient-sdk       | 51.0.8.3  |
+---------------------+-----------+

**What changed**

*resilient* — The ``requests`` library constraint was tightened to ``~= 2.34``
to pick up security and compatibility fixes in the HTTP client layer. If your
app pins ``requests`` directly, ensure your pin is compatible with ``2.34.x``.

*resilient-circuits* — The ``filelock`` dependency was bumped to ``~= 3.29``
to resolve a conflict with newer Python environments.

*resilient-sdk* — The generated ``Dockerfile`` template was updated to use
``python3 -m ensurepip`` for bootstrapping pip inside the container. It also
removes ``pip`` and ``setuptools`` from the final image layer. This reduces
image size and eliminates a common source of CVE findings in container scans.

.. warning::

   **Potential breaking change for custom pipelines that extend the base image.**

   If your pipeline builds on top of ``soarapps-base-docker-image`` and calls
   ``pip install`` at image build or runtime — for example to install additional
   packages into the container — those steps will fail in images built from
   this template because ``pip`` is no longer present after installation.

   **Who is affected:** any team running a custom app pipeline that inherits
   from the IBM SOAR base image and relies on ``pip`` being available inside
   the container.

   **Workaround options:**

   1. **Re-bootstrap pip before using it** — add the following to your
      ``Dockerfile`` before any ``pip install`` step:

      .. code-block:: dockerfile

         RUN python3 -m ensurepip --upgrade

   2. **Pin to the previous base image tag** — if you need more time to
      migrate, reference an explicit earlier tag in your ``FROM`` directive
      rather than ``latest``.

   3. **Pre-install dependencies into the base image** — if you control the
      pipeline, consider building a custom intermediate image with your
      dependencies baked in using the ``ensurepip`` bootstrap approach above,
      then use that as your ``FROM`` target.

   Please raise a support request or open an issue if none of these options
   fit your deployment model.

**Upgrade notes**

- **Standard app developers — action may be required.** If you rebuild your
  app's Docker image, the build process will pull the latest base image which
  no longer includes ``pip``. Any ``RUN pip install`` step in your existing
  ``Dockerfile`` will fail unless you update the template first. Run
  ``resilient-sdk codegen --reload`` to regenerate your ``Dockerfile`` before
  rebuilding. If you are not rebuilding your image, no action is needed.
- **Custom pipeline operators:** review the warning above before upgrading
  to this version of the base image.

----

.. _rn-51.0.8.2:

Version 51.0.8.2
-----------------

*Released June 2026*

This release resolves an intermittent version mismatch issue that caused
packages installed from PyPI to report an incorrect version at runtime. The
fix applies to all four packages. No functional changes were made.

**Package versions**

+---------------------+-----------+
| Package             | Version   |
+=====================+===========+
| resilient           | 51.0.8.2  |
+---------------------+-----------+
| resilient-circuits  | 51.0.8.2  |
+---------------------+-----------+
| resilient-lib       | 51.0.8.2  |
+---------------------+-----------+
| resilient-sdk       | 51.0.8.2  |
+---------------------+-----------+

**What changed**

In previous releases, the package version surfaced at runtime was derived from
git tags via ``setuptools-scm``. Under certain build conditions — particularly
in CI environments where the git tag was not present at build time — this
caused the installed version to be reported as ``0.0.0`` or an incorrect
development version string, even though the correct package was installed.

An explicit ``version`` field has been added to ``setup.cfg`` in all four
packages. This makes the version authoritative and independent of git state,
so the version you see in ``pip show`` and in the logs always matches the
released version.

**Upgrade notes**

No action required. This is a transparent fix — if you were seeing ``0.0.0``
or an unexpected version string in your app logs or when running
``pip show resilient``, upgrading to ``51.0.8.2`` or later will resolve it.
