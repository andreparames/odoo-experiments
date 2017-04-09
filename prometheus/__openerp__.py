# -*- coding: utf-8 -*-
##############################################################################
#    This file is part of the prometheus module.
#
#    prometheus is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    prometheus is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with prometheus. If not, see <http://www.gnu.org/licenses/>.
##############################################################################

{
    'name': 'Prometheus Status Service',
    'version': '9.0.0.0.1',
    'author': 'André Paramés Pereira',
    'category': 'Extra Tools',
    'license': 'LGPL-3',
    'depends': [
        'base',
    ],
    'external_dependencies': {
        'python': [
            'prometheus_client',
        ],
    },
    'installable': True,
}