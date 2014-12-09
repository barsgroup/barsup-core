# coding:utf-8

from os import environ, path

from webob import Response
from webob.dec import wsgify
from webob.static import DirectoryApp


@wsgify
def api(request):
    """WSGI-приложение"""
    return Response('Hello!')


# Приложение, раздающее статику
static_serving_app = DirectoryApp(
    path.join(environ['BUP_PATH'], 'static'),
    index_page='barsup/',
    hide_index_with_redirect=False
)


@wsgify.middleware
def serve_static(request, app):
    url = request.path
    if url == '/' or (
        url.startswith('/barsup')
    ):
        return static_serving_app
    else:
        return app
    # res = request.call_application(static_serving_app)
    # if res[0] != '200 OK':
    #     return app
    # else:
    #     return static_serving_app


application = serve_static(api)
