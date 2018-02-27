.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

==========
s3_storage
==========

This module allows you to use S3 or compatible service (such as
`Minio <https://minio.io/>`_ to store the ir.attachment files, rather than
using the filesystem. It's especially useful for stateless deployments
(e.g. on Docker), since it avoids having to mount a volume or store them
in the database.

NOTE: This module is NOT production-ready!

Installation
============

To install this module, you need to:

#. Install the ``minio`` python library

Configuration
=============

First, you should create an empty Bucket in the S3 service, and get the access
and secret keys. If you're creating a new IAM identity, you can use the following
policy to allow access only to the specific bucket:

::

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListAllMyBuckets"
                ],
                "Resource": "arn:aws:s3:::*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                "Resource": "arn:aws:s3:::BUCKETNAME"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:DeleteObject"
                ],
                "Resource": "arn:aws:s3:::BUCKETNAME/*"
            }
        ]
    }

Then in Odoo, go to Configuration → Technical → System Parameters (you
might have to enable the developer mode first) and configure the following
values:

#. s3_attachment_endpoint: URL of the S3 endpoint
   (ex.: s3.eu-central-1.amazonaws.com)

#. s3_attachment_access_key: Your access key

#. s3_attachment_secret_key: Your secret key

#. s3_attachment_bucket: Name of the bucket

#. s3_attachment_secure: Enable (or not) secure connection. True if not set


When S3 is set, you must copy/move all ir_attachments to S3. To do it, execute
the method _move_to_s3 in the ir.attachment model. You can do it via xmlrpc or
shell. To delete files from the filestore, pass the argument delete_fs as True.
Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/andreparames/odoo-experiments/issues>`_. In case of
trouble, please check there if your issue has already been reported. If you
spotted it first, help us smash it by providing detailed and welcomed feedback.
