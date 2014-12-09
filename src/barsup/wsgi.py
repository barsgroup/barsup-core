# coding:utf-8

from os import environ, path
from sys import stderr, exc_info
from datetime import datetime
import traceback

from webob import Response
from webob.dec import wsgify
from webob.exc import HTTPMovedPermanently, HTTPInternalServerError
from webob.static import DirectoryApp


@wsgify
def api(request):
    """WSGI-приложение"""
    raise ValueError('dasdasd')
    return Response('Hello!')


# Приложение, раздающее статику
static_serving_app = DirectoryApp(
    path.join(environ['BUP_PATH'], 'static'),
    hide_index_with_redirect=True
)


@wsgify.middleware
def serve_static(request, app, prefix):
    url = request.path
    if url == '/':
        raise HTTPMovedPermanently(location=prefix)
    elif url.startswith(prefix):
        return static_serving_app
    else:
        return app


@wsgify.middleware
def catch_errors(request, app, debug=False):
    try:
        return request.call_application(app)
    except Exception:
        trace = ''.join(traceback.format_exception(*exc_info(), limit=20))
        stderr.write('%s\n%s\n' % (
            datetime.now().strftime('%Y.%m.%d/%H:%M:%S'),
            trace
        ))
        if debug:
            params = {'body_template': '<pre>%s</pre>' % trace}
        else:
            params = {}
        raise HTTPInternalServerError(**params)


application = serve_static(
    catch_errors(
        api,
        debug=True
    ),
    prefix='/barsup')


__all__ = (application, api, catch_errors, serve_static)
