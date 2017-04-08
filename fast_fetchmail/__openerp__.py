# coding: utf-8
##############################################################################
#    This file is part of the fast_fetchmail module.
#
#    fast_fetchmail is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    fast_fetchmail is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with fast_fetchmail. If not, see <http://www.gnu.org/licenses/>.
##############################################################################

{
    'name': 'Fast Fetchmail',
    'version': '9.0.0.0.1',
    'author': 'André Paramés Pereira',
    'category': 'mail',
    'license': 'LGPL-3',
    'depends': [
        'fetchmail',
    ],
    'external_dependencies': {
        'python': [
            'recordclass',
        ],
    },
    'installable': True,
}
