import mock
import pytest
import json

from jexia_sdk.http import HTTPClient, HTTPClientError


EXPIRED_TOKEN = ('eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI0ZDBhZGQ4ZC'
                 '1jOTY5LTQ2OGItYmVmYS1jYjJiM2UxNzAxMzgiLCJleHAiOjE1NjY5MTI2M'
                 'DksImlhdCI6MTU2NjkwNTQwOSwiaXNzIjoiYmlmcm9zdCIsInN1YiI6ImFw'
                 'azplNjZhNmVmMS0xZDAyLTRlY2MtYTc2ZS0wZjNhOGVjOWVjZGIifQ.Vv_I'
                 'nZY4_JOhYNLDvL1O63wmOE-CzpusbsT_AadMquhKBTH-3dCd6a1Ty7x1dtv'
                 'E-8w-GwvvXp1X5bMB0ZhLY2u__xjlAZ9xxy2PfXYPWjuv7XLi-FVlfmOwz0'
                 'S1GVG81TINmtGGYHA_d7iuNO0_ZK-fEtHjJycKtHKfXb6PA99vjbpAIgVjk'
                 'Tgb-tnFlLLv1_cUrpPfjMLrL9kReA1Zv6LyEL-MMfQgaLQM30-H-2Bk2daE'
                 'Xgdfbo11F1ohfxE2gw-VQMQ8YoekOu0D9ofmRBdmR7-mmJB09veX8cWRxyy'
                 '__7dlm18RGK1R9f0V59sTwwblz67rztwNvnM4oB5jQQ')
ACTUAL_TOKEN = ('eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiaWZyb3N0Iiw'
                'iaWF0IjoxNTY3Njc4MTg4LCJleHAiOjI4NjE1MTgxODgsImF1ZCI6IjRkMGF'
                'kZDhkLWM5NjktNDY4Yi1iZWZhLWNiMmIzZTE3MDEzOCIsInN1YiI6ImFwazp'
                'lNjZhNmVmMS0xZDAyLTRlY2MtYTc2ZS0wZjNhOGVjOWVjZGIifQ.sJCiRBev'
                'nlZ9has-5ZwUi0ly-V3ev9kFErvIXs_otYA')


class FakeResponse(object):

    def __init__(self, status_code=200, access_token='access-token',
                 refresh_token='refresh-token', raise_for_status=False):
        self.status_code = status_code
        self.text = json.dumps({'access_token': access_token,
                                'refresh_token': refresh_token})
        self._raise_for_status = raise_for_status

    def raise_for_status(self):
        if self._raise_for_status:
            raise Exception('some-error')

    def json(self):
        return json.loads(self.text)


def test_create_http_client():
    client = HTTPClient('test', False)
    assert 'test' == client.domain
    assert not client.ssl_check
    assert client.token_hdr is None
    assert client.base_url is None
    assert client._access_token is None
    assert client._refresh_token is None


@mock.patch('requests.request')
def test_auth_management(mock_req):
    mock_req.return_value = FakeResponse()
    client = HTTPClient('test')
    client.auth_management('test-email', 'test-password')
    mock_req.assert_called_with(
        headers={'User-Agent': 'Jexia SDK HTTP client 1.0',
                 'Accept': 'application/json',
                 'Content-Type': 'application/json'},
        json={'email': 'test-email', 'password': 'test-password'},
        method='POST', params={}, timeout=10,
        url='https://services.test/auth/signin', verify=True)


@mock.patch('requests.request')
def test_auth_management_failed(mock_req):
    mock_req.return_value = FakeResponse(status_code=500,
                                         raise_for_status=True)
    client = HTTPClient('test')
    with pytest.raises(HTTPClientError) as excinfo:
        client.auth_management('test-email', 'test-password')
    assert 'request failed with code 500: ' in str(excinfo.value)


@mock.patch('requests.request')
def test_auth_consumption_apk(mock_req):
    mock_req.return_value = FakeResponse()
    client = HTTPClient('test')
    client.auth_consumption(
        project='123456', method='apk', key='test-key', secret='test-secret')
    mock_req.assert_called_with(
        headers={'User-Agent': 'Jexia SDK HTTP client 1.0',
                 'Accept': 'application/json',
                 'Content-Type': 'application/json'},
        json={'method': 'apk', 'key': 'test-key', 'secret': 'test-secret'},
        method='POST', params={}, timeout=10,
        url='https://123456.app.test/auth', verify=True)


@mock.patch('requests.request')
def test_auth_consumption_ums(mock_req):
    mock_req.return_value = FakeResponse()
    client = HTTPClient('test')
    client.auth_consumption(
        project='123456', method='ums', email='test-email',
        password='test-pass')
    mock_req.assert_called_with(
        headers={'User-Agent': 'Jexia SDK HTTP client 1.0',
                 'Accept': 'application/json',
                 'Content-Type': 'application/json'},
        json={'method': 'ums', 'email': 'test-email', 'password': 'test-pass'},
        method='POST', params={}, timeout=10,
        url='https://123456.app.test/auth', verify=True)


@mock.patch('requests.request')
def test_auth_consumption_incorrect_params(mock_req):
    bad_params = [
        {'project': '12345', 'method': 'apk'},
        {'project': '12345', 'method': 'apk', 'key': 'test-key'},
        {'project': '12345', 'method': 'apk', 'secret': 'test-secret'},
        {'project': '12345', 'method': 'ums'},
        {'project': '12345', 'method': 'ums', 'email': 'test-email'},
        {'project': '12345', 'method': 'ums', 'password': 'test-password'},
        {'project': '12345', 'method': 'bad-method'},
    ]
    mock_req.return_value = FakeResponse()
    client = HTTPClient('test')
    for params in bad_params:
        with pytest.raises(HTTPClientError) as excinfo:
            client.auth_consumption(**params)
        assert 'method' in str(excinfo.value)


@mock.patch('requests.request')
def test__check_token_update_token(mock_req):
    mock_req.return_value = FakeResponse(
        access_token=EXPIRED_TOKEN,
        refresh_token='test-refresh-token')
    client = HTTPClient('test')
    client.auth_management('test-email', 'test-password')
    mock_req.reset_mock()
    client._check_token()
    mock_req.assert_called_with(
        headers={'Authorization': 'Bearer %s' % EXPIRED_TOKEN,
                 'User-Agent': 'Jexia SDK HTTP client 1.0',
                 'Accept': 'application/json',
                 'Content-Type': 'application/json'},
        json={'refresh_token': 'test-refresh-token'},
        method='POST', params={}, timeout=10,
        url='https://services.test/auth/refresh', verify=True)


@mock.patch('requests.request')
def test__check_token(mock_req):
    mock_req.return_value = FakeResponse(
        access_token=ACTUAL_TOKEN,
        refresh_token='test-refresh-token')
    client = HTTPClient('test')
    client.auth_management('test-email', 'test-password')
    mock_req.reset_mock()
    client._check_token()
    mock_req.assert_not_called()
