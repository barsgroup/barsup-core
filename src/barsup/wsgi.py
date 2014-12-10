# coding:utf-8

from os import path
from sys import stderr, exc_info
from datetime import datetime
import traceback
import json
from uuid import uuid4

from webob import Response
from webob.dec import wsgify
from webob.exc import HTTPMovedPermanently, HTTPInternalServerError
from webob.static import DirectoryApp

from barsup import core


def handler(config_file_name, catch_cookies):
    with open(path.expandvars(config_file_name)) as conf:
        api = core.init(
            config=json.load(conf)['container']
        )

    @wsgify
    def app(request):
        params = dict(request.POST)
        for cookie in catch_cookies:
            params[cookie] = request.cookies.get(cookie, None)

        return Response(
            content_type='application/json',
            body=json.dumps(
                api.populate(request.path, **params)
            )
        )

    return app


def static_server(url_prefix, static_path):
    static_app = DirectoryApp(
        path.expandvars(static_path),
        hide_index_with_redirect=True
    )

    @wsgify.middleware
    def mware(request, app):
        url = request.path
        if url == '/':
            raise HTTPMovedPermanently(location=url_prefix)
        elif url.startswith(url_prefix):
            return static_app
        else:
            return app

    return mware


@wsgify.middleware
def catch_errors(request, app, debug=False):
    try:
        return request.get_response(app)
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


@wsgify.middleware
def with_session(request, app, cookie_name, generator):
    if cookie_name not in request.cookies:
        request.cookies[cookie_name] = generator()
    value = request.cookies[cookie_name]
    res = request.get_response(app)
    res.set_cookie(cookie_name, value)
    return res


application = with_session(
    static_server(
        url_prefix='/barsup',
        static_path=path.join('$BUP_PATH', 'static')
    )(
        catch_errors(
            handler(
                config_file_name='$BUP_CONFIG',
                catch_cookies=('web_session_id',),
            ),
            debug=True
        )
    ),
    cookie_name='web_session_id',
    generator=lambda: uuid4().hex
)


__all__ = (application, handler, catch_errors, static_server, with_session)
