# coding: utf-8
##############################################################################
#    This file is part of the s3_storage module.
#
#    s3_storage is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    s3_storage is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with s3_storage. If not, see <http://www.gnu.org/licenses/>.
##############################################################################
from cStringIO import StringIO
import logging

from openerp import api, models, fields
from openerp.tools import human_size

_logger = logging.getLogger(__name__)
try:
    from minio import Minio
    from minio.error import ResponseError
except ImportError:
    _logger.error('minio package is required to store attachments on S3')


class S3AttachmentsToDelete(models.Model):
    _name = 's3.garbage'

    fname = fields.Text()


class S3Attachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def _get_storage_client(self):
        config = self.env['ir.config_parameter'].sudo()
        client = Minio(config.get_param('s3_attachment_endpoint'),
                       access_key=config.get_param('s3_attachment_access_key'),
                       secret_key=config.get_param('s3_attachment_secret_key'),
                       secure=True)
        bucket = config.get_param('s3_attachment_bucket')
        return client, bucket

    @api.model
    def _file_read(self, fname, bin_size=False):
        client, bucket = self._get_storage_client()
        r = ''
        try:
            if bin_size:
                info = client.stat_object(bucket, fname)
                r = human_size(info.size)
            else:
                response = client.get_object(bucket, fname)
                r = response.read().encode('base64')
        except ResponseError as e:
            _logger.info("_read_file (s3) reading %s", fname, exc_info=True)
        return r

    @api.model
    def _file_write(self, value):
        client, bucket = self._get_storage_client()
        bin_value = value.decode('base64')
        fname, _ = self._get_path(bin_value)
        try:
            client.put_object(
                bucket, fname, StringIO(bin_value), len(bin_value))
        except ResponseError as e:
            _logger.info("_file_write (s3) writing %s", fname, exc_info=True)
        return fname

    @api.model
    def _file_gc(self):
        if self._storage() != 'file':
            return
        client, bucket = self._get_storage_client()

        # See comment in the original implementation
        cr = self._cr
        cr.commit()
        self._cr.execute("LOCK ir_attachment IN SHARE MODE")

        self._cr.execute("SELECT fname FROM s3_garbage")
        fnames = [r[0] for r in cr.fetchall()]
        kept = set()
        try:
            errors = client.remove_objects(bucket, fnames)
            for error in errors:
                _logger.info("_file_gc (s3) removing %s: %s - %s",
                             error.object_name,
                             error.error_code,
                             error.error_message)
                kept.add(error.object_name)
            # mark as removed
            self._cr.execute(
                "DELETE FROM s3_garbage WHERE fname NOT IN %s",
                (tuple(kept),))
        except ResponseError as e:
            _logger.info("_file_gc (s3)", exc_info=True)
        cr.commit()
        _logger.info("filestore gc %d checked, %d removed",
                     len(fnames), len(fnames)-len(kept))
 
    @api.model
    def _mark_for_gc(self, fname):
        self._cr.execute("INSERT INTO s3_garbage VALUES (%s) "
                   "ON CONFLICT DO NOTHING")
