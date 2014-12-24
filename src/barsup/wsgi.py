# coding:utf-8

from os import path
from sys import stderr, exc_info
from datetime import datetime
import traceback
import json
from uuid import uuid4

from simplejson.scanner import JSONDecodeError
from webob import Response, exc
from webob.dec import wsgify
from webob.static import DirectoryApp

from barsup import core
from barsup import exceptions
from barsup.util import serialize_to_json, load_configs


def handler(config_file_name, catch_cookies):
    """
    Обработчик HTTP-запросов к приложению
    """
    api = core.init(config=load_configs(config_file_name))

    @wsgify
    def app(request):
        params = {}

        try:
            params.update(request.json)
        except JSONDecodeError:
            params.update(request.params)

        for cookie in catch_cookies:
            params[cookie] = request.cookies.get(cookie, None)

        result = api.populate(
            request.path, **params)

        return Response(
            content_type='application/json',
            body=json.dumps({
                'data': result,
                'success': True
            }, default=serialize_to_json)
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
            raise exc.HTTPMovedPermanently(location=url_prefix)
        elif url.startswith(url_prefix):
            return static_app
        else:
            return app

    return mware


@wsgify.middleware
def catch_errors(request, app, debug=False):
    try:
        return request.get_response(app)

    except exceptions.BadRequest:  # 400
        raise exc.HTTPBadRequest()

    except exceptions.Unauthorized:  # 401
        raise exc.HTTPUnauthorized()

    except exceptions.Forbidden:  # 403
        raise exc.HTTPForbidden()

    except exceptions.NotFound:  # 404
        raise exc.HTTPNotFound()

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
        raise exc.HTTPInternalServerError(**params)


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
