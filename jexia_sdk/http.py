#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import requests
from requests.exceptions import HTTPError

from six.moves.urllib.parse import urlencode
import jwt


LOG = logging.getLogger(__name__)
DEFAULT_DOMAIN = "jexia.com"
URLS = {
    'management': 'https://services.%(domain)s',
    'consumption': 'https://%(project)s.app.%(domain)s',
}
SECRETS = ['password', 'secret']


class HTTPClientError(Exception):
    '''
    Basic exception for HTTPClient errors.
    '''
    pass


class HTTPRequestError(HTTPClientError):
    '''
    Class for HTTP errors if response contains status code 4xx or 5xx.

    :param request_exc: `requests.exceptions.HTTPError` exception
    '''

    def __init__(self, request_exc):
        self.response = request_exc.response
        self.errors = list()
        try:
            for err in self.response.json():
                self.errors.append('%s (req_id: %s)'
                                   % (err['message'], err['request_id']))
        except Exception:
            self.errors.append(self.response.text)
        super(HTTPRequestError, self).__init__(self.errors)

    def __str__(self):
        return '\n'.join(self.errors)


class HTTPClient(object):
    '''
    Class represents HTTP client for Jexia platform.

    >>> client = HttpClient()
    >>> client.auth_management('test@example.com', 'password')

    :param str domain: the main domain of Jexia platform, default to jexia.com
    :param bool ssl_check: enable/disable SSL checking for requests, defaults
        to True
    '''

    def __init__(self, domain=DEFAULT_DOMAIN, ssl_check=True):
        self.domain = domain
        self.ssl_check = ssl_check
        self.token_hdr = None
        self.base_url = None
        self._access_token = None
        self._refresh_token = None

    def auth_management(self, email, password):
        '''
        The method used to authenticate the client on the management level.

        :param str email: email address of Jexia's account
        :param str password: password of Jexia's account
        '''
        self.api_type = 'management'
        self.base_url = URLS[self.api_type] % {'domain': self.domain}
        self._first_auth(email=email, password=password)

    def auth_consumption(self, project, method, key=None, secret=None,
                         email=None, password=None):
        '''
        The method used to authenticate the client on the consumption level.

        :param str project: project of Jexia's account
        :param str method: authentication method, can be 'apk' or 'ums'
        :param str key: application key for the project, required for apk
            method
        :param str secret: application secret for the project, required for apk
            method
        :param str email: user's email address, required for ums method
        :param str password: user's password, required for ums method
        '''
        self.api_type = 'consumption'
        self.base_url = URLS[self.api_type] % {'domain': self.domain,
                                               'project': project}
        if method == 'apk':
            if not key or not secret:
                raise HTTPClientError('key and secret are required '
                                      'parameter for apk authentification'
                                      'method')
            self._first_auth(method=method, key=key, secret=secret)
        elif method == 'ums':
            if not email or not password:
                raise HTTPClientError('email and password are required '
                                      'parameters for ums '
                                      'authentification method')
            self._first_auth(method=method, email=email, password=password)
        else:
            raise HTTPClientError('Unsupported authentication method "%s"'
                                  % method)

    def is_authenticated(self):
        '''
        The method checks the client was authenticated or not.
        '''
        return self.token_hdr is not None

    def request(self, method, url, data=None, headers=None,
                timeout=10, check_token=True, **params):
        '''
        The method to make a request to Jexia's API with authentication.

        :param str method: HTTP method for the request (GET, POST, etc.)
        :param str url: URL to call in the request
        :param dict data: data for JSON body
        :param dict headers: additional headers for request
        :param int timeout: timeout of request, defaults to 10 seconds
        :param bool check_token: disable/enable access token checking before
            request
        :param **params: query params for request
        '''
        if check_token:
            self._check_token()
        if not headers:
            headers = {}
        # Add token to headers
        if self.token_hdr:
            headers = dict(headers, **self.token_hdr)
        # Add common headers
        headers['User-Agent'] = 'Jexia SDK HTTP client 1.0'
        headers['Accept'] = 'application/json'
        # Content-Type header required only for POST request
        if method == 'POST':
            headers['Content-Type'] = 'application/json'
        url = self.base_url + url
        LOG.debug("REQ: %s" % self._make_curl_command(
            url, method, headers, data, params))
        try:
            res = requests.request(
                method=method, url=url, timeout=timeout, json=data,
                headers=headers, params=params, verify=self.ssl_check)
        except Exception as err:
            raise HTTPClientError(err)
        LOG.debug("RES '%s': %s" % (res.status_code, res.text))
        try:
            res.raise_for_status()
        except HTTPError as err:
            raise HTTPRequestError(err)
        if method != 'DELETE':
            return res.json()

    def _make_curl_command(self, url, method, headers, data=None, params=None):
        if data:
            data = data.copy()
            for secret in SECRETS:
                if secret in data:
                    data[secret] = '***'
        curl_cmd = "curl -v {headers} {data} -X {method} \"{url}{params}\""
        curl_headers = ["-H \"%s: %s\"" % (h, v) for h, v in headers.items()]
        curl_data = "-d '%s'" % json.dumps(data) if data else ""
        curl_params = ""
        if params:
            curl_params = "?" + urlencode(params)
        return curl_cmd.format(headers=" ".join(curl_headers),
                               data=curl_data,
                               method=method,
                               url=url,
                               params=curl_params)

    def _check_token(self):
        try:
            # We need to check only expire date
            jwt.decode(self._access_token,
                       options={'verify_exp': True, 'verify_signature': False,
                                'verify_nbf': False, 'verify_iat': False,
                                'verify_aud': False, 'verify_iss': False})
        except jwt.exceptions.ExpiredSignatureError:
            self._update_access_token()

    def _first_auth(self, **kwargs):
        auth_url = '/auth'
        if self.api_type == 'management':
            auth_url += '/signin'
        res = self.request(
            method='POST', url=auth_url, data=kwargs, check_token=False,)
        self._save_tokens(res)

    def _update_access_token(self):
        res = self.request(
            method='POST', url='/auth/refresh', check_token=False,
            data={'refresh_token': self._refresh_token})
        self._save_tokens(res)

    def _save_tokens(self, response):
        if 'access_token' not in response:
            raise HTTPClientError(
                'Fail to get new access token for the account')
        if 'refresh_token' not in response:
            raise HTTPClientError(
                'Fail to get new refresh token for the account')
        self._access_token = response['access_token']
        self._refresh_token = response['refresh_token']
        self.token_hdr = {"Authorization": "Bearer %s" % self._access_token}
