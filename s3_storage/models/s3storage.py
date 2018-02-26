"""ir.attachment extension"""
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

LOGGER = logging.getLogger(__name__)
try:
    from minio import Minio
    from minio.error import ResponseError
except ImportError:
    LOGGER.error('minio package is required to store attachments on S3')


class S3Attachment(models.Model):
    """ir.attachment extension"""
    _inherit = 'ir.attachment'

    @api.model
    def _storage(self):
        """
        Get the storage type.
        In case of missing S3 configurations, the storage defaults to file
        """
        res = super(S3Attachment, self)._storage()
        if res == 's3':
            params = ['s3_attachment_endpoint', 's3_attachment_access_key',
                      's3_attachment_secret_key', 's3_attachment_bucket']
            config = self.env['ir.config_parameter'].sudo()
            for param in params:
                if not config.get_param(param, False):
                    res = 'file'
                    LOGGER.error('Missing S3 configuration: %s', param)
                    break
        return res

    @api.model
    def _get_storage_client(self):
        config = self.env['ir.config_parameter'].sudo()
        secure = config.get_param('s3_attachment_secure', True)
        if isinstance(secure, (str, unicode)):
            secure = True if secure.lower() in ['1', 'true', 't'] else False
        client = Minio(config.get_param('s3_attachment_endpoint'),
                       access_key=config.get_param('s3_attachment_access_key'),
                       secret_key=config.get_param('s3_attachment_secret_key'),
                       secure=secure)
        bucket = config.get_param('s3_attachment_bucket')
        return client, bucket

    @api.model
    def _file_read(self, fname, bin_size=False):
        if self._storage() != 's3':
            return super(S3Attachment, self)._file_read(fname, bin_size)
        client, bucket = self._get_storage_client()
        res = ''
        try:
            if bin_size:
                info = client.stat_object(bucket, fname)
                res = human_size(info.size)
            else:
                response = client.get_object(bucket, fname)
                res = response.read().encode('base64')
        except ResponseError as errn:
            LOGGER.info("_read_file (s3) reading %s", fname, exc_info=True)
        return res

    @api.model
    def _file_write(self, value, checksum):
        if self._storage() != 's3':
            return super(S3Attachment, self)._file_write(value, checksum)
        client, bucket = self._get_storage_client()
        bin_value = value.decode('base64')
        fname, _ = self._get_path(bin_value, checksum)
        try:
            client.put_object(
                bucket, fname, StringIO(bin_value), len(bin_value))
        except ResponseError as errn:
            LOGGER.info("_file_write (s3) writing %s", fname, exc_info=True)
        return fname

    @api.model
    def _file_delete(self, fname):
        if self._storage() != 's3':
            return super(S3Attachment, self)._file_delete(fname)
        client, bucket = self._get_storage_client()

        try:
            errors = client.remove_object(bucket, fname)
            for error in errors:
                LOGGER.info("_file_delete (s3) removing %s: %s - %s",
                            error.object_name,
                            error.error_code,
                            error.error_message)
        except ResponseError as errn:
            LOGGER.info("_file_gc (s3)", exc_info=True)
        LOGGER.info("filestore  %d removed", fname)
        return None
