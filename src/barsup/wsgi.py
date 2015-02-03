# coding:utf-8
"""Функционал для работы уровня WSGI."""

import json
import traceback
from os import path
from datetime import datetime
from uuid import uuid4

from simplejson.scanner import JSONDecodeError
from webob import Response, exc
from webob.dec import wsgify
from webob.static import DirectoryApp

from sys import stderr, exc_info
from barsup import core, exceptions
from barsup.router import RoutingError
from barsup.util import serialize_to_json


def handler(config_file_name, catch_cookies):
    """Обработчик HTTP-запросов к приложению."""
    api = core.init(config=config_file_name)

    @wsgify
    def app(request):
        params = {}

        try:
            params.update(request.json)
        except JSONDecodeError:
            params.update(request.params)

        for cookie in catch_cookies:
            params[cookie] = request.cookies.get(cookie, None)

        status = 200
        try:
            result = api.populate(
                request.path, **params)

        except (exceptions.BadRequest, RoutingError) as e:
            status, result = 400, e

        except exceptions.Unauthorized as e:
            status, result = 401, e

        except exceptions.Forbidden as e:
            status, result = 403, e

        except exceptions.NotFound as e:
            status, result = 404, e

        if status == 200:
            body = json.dumps({'data': result,
                               'success': True},
                              default=serialize_to_json)
        else:
            body = json.dumps(getattr(result, 'values', str(result)))

        return Response(
            content_type='application/json',
            body=body,
            status=status
        )

    return app


def static_server(url_prefix, static_path):
    """MW для статики."""
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
    """MW для конвертации неотловленных исключений."""
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
        raise exc.HTTPInternalServerError(**params)


@wsgify.middleware
def with_session(request, app, cookie_name, generator):
    """MW для контроля cookies."""
    if cookie_name not in request.cookies:
        request.cookies[cookie_name] = generator()
    value = request.cookies[cookie_name]
    res = request.get_response(app)
    res.set_cookie(cookie_name, value)
    return res


def make_application():
    """
    Возвращает преднастроенный wsgi app.

    Можно использовать в конечных приложениях
    """
    return with_session(
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


__all__ = ('make_application', 'handler', 'catch_errors',
           'static_server', 'with_session')
