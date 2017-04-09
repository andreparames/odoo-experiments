.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

==========
prometheus
==========

This module allows you to publish the current server status for monitoring by
a system such as `Prometheus <https://prometheus.io/>`_. Currently it only
publishes the rpc response times by database, besides the default metrics (CPU
usage, RAM, file descriptors and start time).

NOTE: This module is NOT production-ready!

Installation
============

To install this module, you need to:

#. Install the `prometheus_client` python library

Configuration
=============

After you install the module, metrics will be published at `/serverstatus`.
Just point your Prometheus server at that URL to start collecting.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/andreparames/odoo-experiments/issues>`_. In case of
trouble, please check there if your issue has already been reported. If you
spotted it first, help us smash it by providing detailed and welcomed feedback.
