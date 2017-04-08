.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

==============
fast_fetchmail
==============

This module speeds up the responsiveness of the fetchmail functionality,
by using the IMAP IDLE feature that allows servers to notify clients of
new emails in real-time.

NOTE: This module is NOT production-ready!

Installation
============

To install this module, you need to:

#. Install the `recordclass` python library

Configuration
=============

You can just configure the fetchmail module as usual. If any of the IMAP
servers supports IDLE, it'll be used to speed up the process.

Technical Information
=====================

This module starts a single new thread, in which it'll connect to each
server and run the IDLE command to be notified of new messages. It then
uses using select() to wait for a notification from any of the connections,
upon which the session is resumed to sync the new messages.

Why select() and not epoll()
----------------------------

Since the number of servers is generally low, the performance drawbacks of
select() are minimal, so it was chosen for its superior platform
compatibility.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/andreparames/odoo-experiments/issues>`_. In case of
trouble, please check there if your issue has already been reported. If you
spotted it first, help us smash it by providing detailed and welcomed feedback.

