# coding: utf-8
import json

import pytest

from _pytest.python import fixture

from webob import Request, exc

from barsup.wsgi import handler


@fixture
def process(request):
    return handler(
        config_file_name='$BUP_CONFIG',
        catch_cookies=('something-cookies',),
    )(request)


def test_handler():
    request = Request.blank(
        '/controller/success',
        content_type='application/json',
        charset='utf-8',
        method='POST')

    response = process(request)
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert response.json['data'] is True
    assert response.json['success'] is True


def test_wrong_controller():
    request = Request.blank(
        '/wrong-controller/success',
        content_type='application/json',
        charset='utf-8',
        method='POST')

    with pytest.raises(exc.HTTPBadRequest):
        process(request)


def test_with_json_body():
    request = Request.blank(
        '/controller/with_data',
        content_type='application/json',
        charset='utf-8',
        method='POST',
        body=json.dumps({"filter": [1, 2, 3], "sorter": "desc"}).encode(
            'utf-8'))

    response = process(request)
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)

    data = response.json['data']
    assert data['filter'] == [1, 2, 3]
    assert data['sorter'] == 'desc'
    assert response.json['success'] is True


def test_with_post_body():
    request = Request.blank(
        '/controller/with_data',
        charset='utf-8',
        method='POST',
    )
    request.body = 'one=a&two=b&three=bar'.encode('utf-8')

    response = process(request)
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)

    data = response.json['data']
    assert data['one'] == 'a'
    assert data['two'] == 'b'
    assert data['three'] == 'bar'
    assert response.json['success'] is True


def test_unauthorized():
    request = Request.blank(
        '/unauthorized',
    )
    with pytest.raises(exc.HTTPUnauthorized):
        process(request)


def test_forbidden():
    request = Request.blank(
        '/forbidden',
    )
    with pytest.raises(exc.HTTPForbidden):
        process(request)


def test_not_found():
    request = Request.blank(
        '/not-found',
    )
    with pytest.raises(exc.HTTPNotFound):
        process(request)


def test_value_error():
    request = Request.blank(
        '/value-error',
    )
    with pytest.raises(ValueError):
        process(request)


def test_wrong_serialize():
    request = Request.blank(
        '/wrong-serialize',
    )
    with pytest.raises(TypeError):
        process(request)
