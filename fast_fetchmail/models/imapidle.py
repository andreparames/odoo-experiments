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
import threading
import logging
from select import select
from threading import Thread
from time import time

from openerp import models, fields, api, registry, SUPERUSER_ID

_logger = logging.getLogger('fast_fetchmail')
try:
    from recordclass import recordclass
except ImportError:
    _logger.error('recordclass is required')

NINE_MINUTES = 9 * 60
Pair = recordclass('Pair', ['coroutine', 'connection'])


class CantIDLE(Exception):
    """ Server doesn't support IDLE extension """
    pass


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    can_idle = fields.Boolean()

    @api.model
    def create(self, vals):
        vals['can_idle'] = (vals.get('type') == 'imap')
        return super(FetchmailServer, self).create(vals)

    @api.model
    def _fetch_mails(self, ids=False):
        """ starts IDLing thread if not running,
        and processes non-IDLE servers """
        self.run_imap_idle()
        if ids:
            recs = self.browse(ids)
        else:
            recs = self.search([
                ('state', '=', 'done'),
                ('type', 'in', ['pop', 'imap']),
                ('can_idle', '=', False),
            ])
        return recs.fetch_mail()

    def _start_idling(self, connection):
        _logger.debug('%s: Started IDLing', connection.host)
        tag = connection._new_tag()
        connection.send("%s IDLE\r\n" % tag)
        connection.readline()
        connection.idle_start = time()

    def _stop_idling(self, connection):
        _logger.debug('%s: Stopped IDLing', connection.host)
        connection.send("DONE\r\n")
        connection.readline()

    @api.multi
    def _fetch(self, connection):
        _logger.warn('%s: Fetching', connection.host)
        self.ensure_one()
        mail_thread = self.env['mail.thread']
        result, data = connection.search(None, '(UNSEEN)')
        count, failed = 0, 0
        for num in data[0].split():
            res_id = None
            result, data = connection.fetch(num, '(RFC822)')
            connection.store(num, '-FLAGS', '\\Seen')
            try:
                res_id = mail_thread.message_process(
                    self.object_id.model,
                    data[0][1],
                    save_original=self.original,
                    strip_attachments=(not self.attach))
            except Exception:
                _logger.exception(
                    'Failed to process mail from %s server %s.',
                    self.type, self.name)
                failed += 1
            if res_id and self.action_id:
                model = self._context.get("thread_model", self.object_id.model)
                self.action_id.run({
                    'active_id': res_id,
                    'active_ids': [res_id],
                    'active_model': model,
                })
            connection.store(num, '+FLAGS', '\\Seen')
            self._cr.commit()
            count += 1
        _logger.info("Fetched %d email(s) on %s server %s; "
                     "%d succeeded, %d failed.",
                     count, self.type, self.name, (count - failed), failed)

    @api.multi
    def _run(self):
        self.ensure_one()
        state = 'disconnected'
        connection = None
        while True:
            if connection:
                _logger.warn('%s: State: %s', connection.host, state)
            if state == 'disconnected':
                connection = self.connect()
                if 'IDLE' not in connection.capabilities:
                    _logger.warn('Server %s doesn\'t support IDLE, '
                                 'falling back to polling',
                                 connection.host)
                    self.write({'can_idle': False})
                    raise CantIDLE()
                connection.select()
                state = 'connected'
            elif state == 'connected':
                try:
                    self._fetch(connection)
                    state = 'synced'
                except Exception as e:
                    _logger.error('%s: Error fetching: %s', connection.host, e)
                    state = 'disconnected'
            elif state == 'synced':
                # idle
                res = yield connection
                if res == 'new':
                    state = 'connected'
                elif res in ('disconnected', 'closing'):
                    state = res
                else:
                    state = 'synced'
            elif state == 'closing':
                try:
                    connection.logout()
                except Exception as e:
                    _logger.info('%s: Error shutting down: %s',
                                 connection.host, e)
                state = 'disconnected'

    @api.model
    def _get_pairs(self, servers):
        pairs = []
        for server in self:
            try:
                coroutine = server._run()
                connection = next(coroutine)
                self._start_idling(connection)
                pairs.append(Pair(coroutine, connection))
            except CantIDLE:
                pass
        return pairs

    def _servers_config_changed(self, since):
        self.env['fetchmail.server'].invalidate_cache(['write_date'])
        all_servers = self.env['fetchmail.server'].search([])
        return any(s.write_date > since for s in all_servers)

    @api.multi
    def _idlemany(self):
        pairs = self._get_pairs(servers=self)
        configcheck = fields.Datetime.now()
        while True:
            self._cr._cnx.rollback()  # to avoid leaving transactions open
            sockets = [p.connection.sock for p in pairs]
            _logger.debug('Select\'ing on %s sockets', len(sockets))
            ready = select(sockets, [], [], 60)[0]
            for sock in ready:
                pair = next(p for p in pairs if p.connection.sock == sock)
                resp = pair.connection.readline()
                _logger.debug('%s: Got %s', p.connection.host, resp)
                if resp == '':  # closed connection
                    pair.connection = pair.coroutine.send('disconnected')
                elif 'EXISTS' in resp:
                    self._stop_idling(pair.connection)
                    pair.connection = pair.coroutine.send('new')
                    self._start_idling(pair.connection)
            for pair in pairs:
                connection = pair.connection
                if (time() - connection.idle_start) > NINE_MINUTES:
                    _logger.debug('%s: Timeout, re-idling', connection.host)
                    self._stop_idling(connection)
                    self._start_idling(connection)
            if self._servers_config_changed(since=configcheck):
                _logger.debug('Config changed, reconnecting...')
                for pair in pairs:
                    self._stop_idling(pair.connection)
                    pair.coroutine.send('closing')
                pairs = self._get_pairs(servers=self)
                configcheck = fields.Datetime.now()

    @api.model
    def run_imap_idle(self):
        for thread in threading.enumerate():
            if thread.name == 'fetchmail_idling' and thread.is_alive():
                return
        server_obj = self.env['fetchmail.server']
        idling_count = server_obj.search([
            ('state', '=', 'done'),
            ('can_idle', '=', True),
        ], count=True)
        if idling_count == 0:
            return
        db_name = self._cr.dbname
        Thread(
            name='fetchmail_idling',
            target=_start_idling_thread,
            args=(db_name,)
        ).start()


def _start_idling_thread(db_name):
    with api.Environment.manage():
        cr = registry(db_name).cursor()
        try:
            env = api.Environment(cr, SUPERUSER_ID, {})
            server_obj = env['fetchmail.server']
            servers = server_obj.search([
                ('state', '=', 'done'),
                ('can_idle', '=', True),
            ])
            servers._idlemany()
        finally:
            try:
                cr.close()
            except Exception:
                pass
