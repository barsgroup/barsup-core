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
    path.join(environ['BUP_PATH'], 'static', 'barsup'),
    index_page='index.html',
    hide_index_with_redirect=True
)


@wsgify.middleware
def serve_static(request, app):
    # url = request.path
    # if url == '/' or (
    #     url.startswith('/index') or
    #     url.startswith('/static/')
    # ):
    #     return static_serving_app
    # else:
    #     return app
    res = request.call_application(static_serving_app)
    if res[0] != '200 OK':
        return app
    else:
        return static_serving_app


application = serve_static(api)
