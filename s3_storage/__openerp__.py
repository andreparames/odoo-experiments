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

{
    'name': 'S3 Storage Backend',
    'version': '9.0.0.0.1',
    'category': 'base',
    'author': 'André Paramés Pereira,Hugo Rodrigues',
    'license': 'LGPL-3',
    'depends': [
        'base',
    ],
    'external_dependencies': {
        'python': [
            'minio',
        ],
    },
    'installable': True,
}
