# coding:utf-8

from os import environ, path

from webob import Response
from webob.dec import wsgify
from webob.exc import HTTPMovedPermanently
from webob.static import DirectoryApp


@wsgify
def api(request):
    """WSGI-приложение"""
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


application = serve_static(api, prefix='/barsup')
