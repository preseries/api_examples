# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2011 BigML, Inc
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
##############################################################################
import logging
import time
import httplib2
import json
import socket
import os

LOGGER = logging.getLogger('sky')

DEFAULT_INITIAL_TIMEOUT = 180  # seconds

PRESERIES_PROTOCOL = os.getenv("PRESERIES_PROTOCOL", "https")
PRESERIES_HOST = os.getenv("PRESERIES_HOST", "preseries.io")
PRESERIES_PORT = os.getenv("PRESERIES_PORT", 80)
PRESERIES_API_VERSION = os.getenv("PRESERIES_API_VERSION", "zion")

PRESERIES_COMPANIES_SEARCH_ENDPOINT = "/company_search"
PRESERIES_PORTFOLIO_ENDPOINT = "/portfolio"

PRESERIES_USERNAME = os.getenv("PRESERIES_USERNAME", None)
PRESERIES_API_KEY = os.getenv("PRESERIES_API_KEY", None)

if not PRESERIES_USERNAME:
    raise Exception(
        "The PRESERIES_USERNAME environment variable must be set")

if not PRESERIES_API_KEY:
    raise Exception(
        "The PRESERIES_API_KEY environment variable must be set")

URL = (PRESERIES_PROTOCOL + '://' + PRESERIES_HOST + ':' +
       PRESERIES_PORT + '/' + PRESERIES_API_VERSION + '/')

COMPANIES_SEARCH_PATH = 'company_search/'
COMPANIES_DATA_PATH = 'company_data/'
COMPANIES_COMPETITORS_PATH = 'company_competitor/'
COMPANIES_SIMILAR_PATH = 'company_similar/'
USER_PORTFOLIO_PATH = 'portfolio/'
USER_PORTFOLIO_COMPANY_PATH = 'portfolio_company/'
USER_STARRED_PATH = 'starred/'
USER_FOLLOWED_PATH = 'following_company/'

SEND_JSON = {'Content-Type': 'application/json'}
ACCEPT_JSON = {'Accept': 'application/json;charset=utf-8'}


# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_PAYMENT_REQUIRED = 402
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_LENGTH_REQUIRED = 411
HTTP_INTERNAL_SERVER_ERROR = 500

CACHE_PRESERIES = True
CACHE_PRESERIES_DIR = "preseries_cache"
GZIP_PRESERIES_CONTENT = "preseries_cache"

MAX_RETRIES = 5
MIN_TIME_BETWEEN_RETRIES = 3


class PreSeriesAPI(object):

    def __init__(self, username=PRESERIES_USERNAME, api_key=PRESERIES_API_KEY,
                 cache=False, timeout=DEFAULT_INITIAL_TIMEOUT):

        socket.setdefaulttimeout(DEFAULT_INITIAL_TIMEOUT)

        if CACHE_PRESERIES and cache:
            self.http = httplib2.Http(
                CACHE_PRESERIES_DIR, timeout=timeout)
        else:
            self.http = httplib2.Http(timeout=timeout)

        self.username = username
        self.api_key = api_key
        self.with_api_key = True

        self.auth = '?username=%s;api_key=%s;' % \
                    (self.username, self.api_key)

    def get(self, path, headers, query_string=''):
        """Retrieves a resource.

        """
        # dummy_param = "dummy__exact=%s" % settings.DUMMY_DATA
        #
        # query_string += '&%s' % dummy_param if len(query_string) > 0 else \
        #     '%s' % dummy_param

        internal_query_string = ''
        if self.with_api_key:
            internal_query_string = '%s' % self.auth
            if len(query_string) > 0:
                internal_query_string += "&%s" % query_string
        elif len(query_string) > 0:
            internal_query_string += "?%s" % query_string

        if len(internal_query_string) > 0:
            path += internal_query_string

        retries = 0
        while True:
            pending_retries = MAX_RETRIES - retries
            try:
                if __debug__:
                    LOGGER.info('========= PRESERIES.IO REQUEST =========')
                    LOGGER.info(path)
                    LOGGER.info(headers)

                start_request_time = time.time()
                response, resource = self.http.request(path, headers=headers)
                if __debug__:
                    LOGGER.info('========= PRESERIES.IO RESPONSE (%s seconds) '
                                '=========' %
                                (time.time() - start_request_time))
                    LOGGER.info(response)
                    LOGGER.debug(resource)
                status = int(response.get('status'))
                if status in [HTTP_OK, HTTP_BAD_REQUEST]:
                    resource = json.loads(resource, 'utf-8')
                    return resource
                elif status in [HTTP_NOT_FOUND]:
                    return None
                else:
                    LOGGER.error("[{0} retries left] PRESERIES.IO is severely "
                                 "broken! {1} {2}".format(pending_retries,
                                                          status, resource))
                    return None
            except httplib2.HttpLib2Error as exception:
                LOGGER.error("[{0} retries left]  Cannot connect to "
                             "PRESERIES.IO [{1}] {2} ".
                             format(pending_retries, path, exception))
                if retries < MAX_RETRIES:
                    retries += 1
                    time.sleep(retries * MIN_TIME_BETWEEN_RETRIES)
                else:
                    return None
            except socket.timeout:
                LOGGER.error(
                    "[{0} retries left] Timeout connecting to PRESERIES.IO "
                    "[{1}]. Almost there!".format(pending_retries, path))
                if retries < MAX_RETRIES:
                    retries += 1
                    time.sleep(retries * MIN_TIME_BETWEEN_RETRIES)
                else:
                    return None
            except socket.error:
                LOGGER.error(
                    "[{0} retries left] Cannot connect to Apian_pre_s [{1}]".
                    format(pending_retries, path))
                if retries < MAX_RETRIES:
                    retries += 1
                    time.sleep(retries * MIN_TIME_BETWEEN_RETRIES)
                else:
                    return None

    def _list(self, url, query_string=''):
        """List resources
        """
        code = HTTP_INTERNAL_SERVER_ERROR
        meta = None
        resources = None
        error = {
            "status": {
                "code": code,
                "message": "The resource couldn't be listed"}}

        LOGGER.info('========= PRESERIES.IO REQUEST =========')
        LOGGER.info(url + self.auth + query_string)
        try:
            start_request_time = time.time()
            response, content = self.http.request(
                url + self.auth + query_string,
                headers=ACCEPT_JSON)

            LOGGER.info('========= PRESERIES.IO RESPONSE (%s seconds) '
                        '=========' % (time.time() - start_request_time))
            LOGGER.info(response)
            LOGGER.debug(content)

            code = int(response.get('status'))

            if code == HTTP_OK:
                resource = json.loads(content, 'utf-8')
                if 'meta' in resource:
                    meta = resource['meta']
                    resources = resource['objects']
                else:
                    meta = None
                    resources = [resource]
                error = {}
            elif code in [HTTP_BAD_REQUEST, HTTP_UNAUTHORIZED, HTTP_NOT_FOUND]:
                error = json.loads(content, 'utf-8')
            else:
                LOGGER.error("Unexpected error (%s)" % code)
                code = HTTP_INTERNAL_SERVER_ERROR

        except ValueError:
            LOGGER.error("Malformed response")
        except httplib2.HttpLib2Error:
            LOGGER.error("Connection error")
        except socket.timeout:
            LOGGER.error("Connection timeout")
        except socket.error:
            LOGGER.error("Error establishing connection")

        return {
            'code': code,
            'meta': meta,
            'resources': resources,
            'error': error}

    def _create(self, url, body, query_string=''):
        """Create a new resource
        """
        code = HTTP_INTERNAL_SERVER_ERROR
        resource_id = None
        location = None
        resource = None
        error = {
            "status": {
                "code": code,
                "message": "The resource couldn't be created"}}
        LOGGER.info('+++++++++ PRESERIES.IO REQUEST +++++++++')
        LOGGER.info('POST ' + url + ';' + query_string)
        LOGGER.info(body)
        try:
            start_request_time = time.time()
            response, content = self.http.request(
                url + self.auth + query_string, 'POST',
                headers=SEND_JSON,
                body=body)

            LOGGER.info('+++++++++ PRESERIES.IO RESPONSE (%s seconds) '
                        '+++++++++' % (time.time() - start_request_time))
            LOGGER.info(response)
            LOGGER.debug(content)

            code = int(response.get('status'))

            if code in [HTTP_CREATED, HTTP_OK]:
                error = {}
                location = response.get('location')
                resource = None
                resource_id = None

                if content:
                    resource = json.loads(content, 'utf-8')
                    resource_id = resource['id']
                elif location:
                    resource_id = location[location.rfind('/')+1:]
            elif code in [
                    HTTP_BAD_REQUEST,
                    HTTP_UNAUTHORIZED,
                    HTTP_PAYMENT_REQUIRED]:
                error = json.loads(content, 'utf-8')
            elif code == HTTP_OK and \
                    json.loads(content, 'utf-8').get('status'):
                error = json.loads(content, 'utf-8')
                location = None
                resource = None
                resource_id = None
            else:
                LOGGER.error("Unexpected error (%s)" % code)
                code = HTTP_INTERNAL_SERVER_ERROR

        except ValueError:
            LOGGER.error("Malformed response")
        except httplib2.HttpLib2Error:
            LOGGER.error("Connection error")
        except socket.timeout:
            LOGGER.error("Connection timeout")
        except socket.error:
            LOGGER.error("Error establishing connection")
        except Exception as ex:
            LOGGER.error("Error:  %s" % ex)

        return {
            'code': code,
            'id': resource_id,
            'location': location,
            'resource': resource,
            'error': error}

    def _get(self, url, query_string=''):
        """Retrieve a resource
        """
        code = HTTP_INTERNAL_SERVER_ERROR
        resource_id = None
        location = url
        resource = None
        error = {
            "status": {
                "code": code,
                "message": "The resource couldn't be retrieved"}}

        try:
            LOGGER.info('========= PRESERIES.IO REQUEST =========')
            LOGGER.info(url + self.auth + query_string)

            start_request_time = time.time()
            response, content = self.http.request(
                url + self.auth + query_string,
                headers=ACCEPT_JSON)

            LOGGER.info('========= PRESERIES.IO RESPONSE (%s seconds) '
                        '=========' % (time.time() - start_request_time))
            LOGGER.info(response)
            LOGGER.debug(content)

            code = int(response.get('status'))

            if code == HTTP_OK:
                resource = json.loads(content, 'utf-8')
                if 'id' in resource:
                    resource_id = resource['id']
                error = {}
            elif code in [HTTP_BAD_REQUEST, HTTP_UNAUTHORIZED, HTTP_NOT_FOUND]:
                error = json.loads(content, 'utf-8')
            else:
                LOGGER.error("Unexpected error (%s)" % code)
                code = HTTP_INTERNAL_SERVER_ERROR

        except ValueError:
            LOGGER.error("Malformed response")
        except httplib2.HttpLib2Error:
            LOGGER.error("Connection error")
        except socket.timeout:
            LOGGER.error("Connection timeout")
        except socket.error:
            LOGGER.error("Error establishing connection")

        return {
            'code': code,
            'id': resource_id,
            'location': location,
            'resource': resource,
            'error': error}

    def _update(self, url, body, query_string=''):
        """Update a resource
        """
        code = HTTP_INTERNAL_SERVER_ERROR
        resource_id = None
        location = url
        resource = None
        error = {
            "status": {
                "code": code,
                "message": "The resource couldn't be updated"}}

        try:
            LOGGER.info('////////// PRESERIES.IO REQUEST ///////////')
            LOGGER.info('PUT ' + url)
            LOGGER.info(body)

            start_request_time = time.time()
            response, content = self.http.request(
                url + self.auth + query_string, 'PUT',
                headers=SEND_JSON,
                body=body)

            LOGGER.info('////////// PRESERIES.IO RESPONSE (%s seconds) '
                        '//////////' % (time.time() - start_request_time))
            LOGGER.info(response)
            LOGGER.debug(content)

            code = int(response.get('status'))

            if code in [HTTP_ACCEPTED, HTTP_OK, HTTP_NO_CONTENT]:
                location = response.get('location')
                resource = json.loads(content, 'utf-8')
                resource_id = resource['id']
                error = {}
            elif code in [HTTP_UNAUTHORIZED,
                          HTTP_PAYMENT_REQUIRED,
                          HTTP_METHOD_NOT_ALLOWED]:
                error = json.loads(content, 'utf-8')
            else:
                LOGGER.error("Unexpected error (%s)" % code)
                code = HTTP_INTERNAL_SERVER_ERROR

        except ValueError:
            LOGGER.error("Malformed response")
        except httplib2.HttpLib2Error:
            LOGGER.error("Connection error")
        except socket.timeout:
            LOGGER.error("Connection timeout")
        except socket.error:
            LOGGER.error("Error establishing connection")

        return {
            'code': code,
            'id': resource_id,
            'location': location,
            'resource': resource,
            'error': error}

    def _delete(self, url):
        """Delete a resource
        """
        code = HTTP_INTERNAL_SERVER_ERROR
        error = {
            "status": {
                "code": code,
                "message": "The resource couldn't be deleted"}}
        try:
            LOGGER.info('------------- PRESERIES.IO REQUEST -------------')
            LOGGER.info('DELETE ' + url)

            start_request_time = time.time()
            response, content = self.http.request(
                url + self.auth, 'DELETE')

            code = int(response.get('status'))

            LOGGER.info('------------- PRESERIES.IO RESPONSE (%s seconds) '
                        '-------------' % (time.time() - start_request_time))
            LOGGER.info(code)

            if code == HTTP_NO_CONTENT:
                error = {}
            elif code in [HTTP_BAD_REQUEST, HTTP_UNAUTHORIZED, HTTP_NOT_FOUND]:
                error = json.loads(content, 'utf-8')
            else:
                LOGGER.error("Unexpected error (%s)" % code)
                code = HTTP_INTERNAL_SERVER_ERROR

        except ValueError:
            LOGGER.error("Malformed response")
        except httplib2.HttpLib2Error:
            LOGGER.error("Connection error")
        except socket.timeout:
            LOGGER.error("Connection timeout")
        except socket.error:
            LOGGER.error("Error establishing connection")

        return {
            'code': code,
            'error': error}

    ##########################################################################
    #
    # Company Endpoints
    #
    ##########################################################################

    def search_companies(self, path=COMPANIES_SEARCH_PATH, query_string='',
                         headers=ACCEPT_JSON):
        """Retrieves a source using query_string.

        """
        url = URL + path
        return self.get(url, headers, query_string)

    def get_company_data(self, query_string='',
                         path=COMPANIES_DATA_PATH):
        """Retrieves the stats of all the companies using query_string.

        """
        url = URL + path
        return self._list(url, query_string)

    def get_companies_competitors(
            self, query_string='',
            path=COMPANIES_COMPETITORS_PATH):
        """Retrieves the competitors of the requested company using
        query_string.

        """
        url = URL + path
        return self._list(url, query_string)

    def get_companies_similar(
            self, query_string='',
            path=COMPANIES_SIMILAR_PATH):
        """Retrieves the similar of the requested company using
        query_string.

        """
        url = URL + path
        return self._list(url, query_string)

    ##########################################################################
    #
    # User Portfolios
    #
    ##########################################################################

    def get_portfolios(self, path=USER_PORTFOLIO_PATH, query_string=''):
        """Retrieves portfolios.

        """
        return self._list(URL + path, query_string)

    def get_portfolio(self, portfolio, query_string=''):
        """Retrieve a portfolio
        """
        return self._get("%s/%s" % (URL + USER_PORTFOLIO_PATH, portfolio),
                         query_string=query_string)

    def create_portfolio(self, name, companies=None):
        """Creates a portfolio
        """
        params = {'name': name}
        if companies:
            params['companies'] = companies

        body = json.dumps(params)
        return self._create(URL + USER_PORTFOLIO_PATH, body)

    def delete_portfolio(self, portfolio):
        """Deletes a portfolio
        """
        return self._delete("%s/%s" % (URL + USER_PORTFOLIO_PATH, portfolio))

    def update_portfolio(self, portfolio, changes):
        """Updates a portfolio
        """
        body = json.dumps(changes)
        return self._update(
            "%s/%s" % (URL + USER_PORTFOLIO_PATH, portfolio), body)

    def portfolio_add_company(self, portfolio, company_id):
        """Adds a company to portfolio
        """
        body = json.dumps({})
        url = '%s/%s/companies/add/%s' % \
              (URL + USER_PORTFOLIO_PATH, portfolio, company_id)
        return self._create(url, body)

    def portfolio_remove_company(self, portfolio, company_id):
        """Removes a company from portfolio
        """
        url = '%s/%s/companies/delete/%s' % \
              (URL + USER_PORTFOLIO_PATH, portfolio, company_id)
        return self._delete(url)

    def get_portfolio_companies(self, query_string=''):
        """Retrieves the companies in a portfolio.

        """
        return self._list(URL + USER_PORTFOLIO_COMPANY_PATH, query_string)

    ##########################################################################
    #
    # User Starred Companies
    #
    ##########################################################################
    def get_starred_companies(self, query_string=''):
        """Retrieves starred companies.

        """
        return self._list(URL + USER_STARRED_PATH, query_string)

    def create_starred(self, company_id, company_name, args=None):
        """Create a starred company
        """
        if args is None:
            args = {}
        args.update({
            "company_id": company_id,
            "company_name": company_name
        })

        body = json.dumps(args)
        return self._create(URL + USER_STARRED_PATH, body)

    def delete_starred(self, starred):
        """Removes a starred company
        """
        return self._delete("%s/%s" % (URL + USER_STARRED_PATH, starred))

    ##########################################################################
    #
    # User Followed Companies
    #
    ##########################################################################
    def get_followed_companies(self, query_string=''):
        """Retrieves followed companies.

        """
        return self._list(URL + USER_FOLLOWED_PATH, query_string)

    def create_followed(self, company_id, company_name, args=None):
        """Create a followed company
        """
        if args is None:
            args = {}
        args.update({
            "company_id": company_id,
            "company_name": company_name
        })

        body = json.dumps(args)
        return self._create(URL + USER_FOLLOWED_PATH, body)

    def delete_followed(self, followed):
        """Removes a followed company
        """
        return self._delete("%s/%s" % (URL + USER_FOLLOWED_PATH, followed))
