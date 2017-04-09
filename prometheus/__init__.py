import logging
import threading
from werkzeug.wsgi import DispatcherMiddleware

from openerp import http
from openerp.http import JsonRequest, HttpRequest
import openerp

_logger = logging.getLogger(__name__)
try:
    from prometheus_client import make_wsgi_app, Histogram
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    _logger.error('You must install the prometheus library.')

if HAS_PROMETHEUS:
    rpc_histogram = Histogram(
        'rpc_response_seconds', 'RPC Response time', ['database'])

    class MonitoredRequest(object):
        def dispatch(self):
            dbname = getattr(threading.currentThread(), 'dbname', 'N/A')
            with rpc_histogram.labels(database=dbname).time():
                return super(MonitoredRequest, self).dispatch()

    class MonitoredJsonRequest(MonitoredRequest, JsonRequest):
        pass

    class MonitoredHttpRequest(MonitoredRequest, HttpRequest):
        pass

    def get_request(httprequest):
        # deduce type of request
        if httprequest.args.get('jsonp'):
            return MonitoredJsonRequest(httprequest)
        if httprequest.mimetype in ("application/json",
                                    "application/json-rpc"):
            return MonitoredJsonRequest(httprequest)
        else:
            return MonitoredHttpRequest(httprequest)

    http.root.get_request = get_request

    try:
        odoo_app = openerp.service.wsgi_server.application
        monitor_app = make_wsgi_app()
        combined_app = DispatcherMiddleware(odoo_app, {
            '/serverstatus': monitor_app,
        })
        openerp.service.server.server.app = combined_app
    except Exception as e:
        _logger.error('Error starting server: %s', e)
