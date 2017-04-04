from __future__ import unicode_literals
from functools import reduce
import operator
import requests
import json

from netmiko.json_exception import NetMikoRequestsTimeoutException, NetMikoRequestsHTTPException


class JsonConnection(object):
    def __init__(self, ip='', host='', username='', password='',
                 port=80, device_type='', verbose=False, timeout=8):
        if ip:
            self.host = ip
            self.ip = ip
        elif host:
            self.host = host
        if not ip and not host:
            raise ValueError("Either ip or host must be set")
        self.port = int(port)
        self.username = username
        self.password = password
        self.device_type = device_type
        self.timeout = timeout

        self.headers = {'Content-Type': 'application/json'}
        self.jsonrpc_id = 0
        self.cookie = None
        self.json_request = {}
        self.url = None
        self.result_path = []

        self.construct_params()

    def set_url(self, url=None):
        self.url = url

    def set_json_request(self, request=None):
        self.json_request = request

    def set_result_path(self, path=None):
        self.result_path = path

    def construct_params(self):
        self.set_url()
        self.set_json_request()
        self.set_result_path()

    def send_command(self, command_string):
        # in JSONRCP transactions to avoid re-authenticating for every transaction
        # if we have a cookie from previous authentication, use it
        if self.cookie is not None:
            self.headers['Cookie'] = 'session={0}'.format(self.cookie)

        # increment the JSONRPC transaction counter
        self.jsonrpc_id += 1
        self.json_request['id'] = self.jsonrpc_id

        try:
            self.json_request['params']['cmd'] = [command_string]
        except TypeError:
            self.json_request['params'] = [command_string]

        # send the JSONRPC message
        try:
            response = requests.post(self.url,
                                     headers=self.headers,
                                     auth=(self.username, self.password),
                                     data=json.dumps(self.json_request),
                                     timeout=3)
        except requests.ConnectTimeout as e:
        # except requests.RequestException as e:
            # return "Error at json requesting: {}".format(e)
            raise NetMikoRequestsTimeoutException("Error at json requesting: {}".format(e))
        # first check the HTTP error code to see if HTTP was successful
        # delivering the message
        # if response.status_code == requests.codes.ok:
        try:
            response.status_code == requests.codes.ok
            # if we have a cookie, store it so we can use it later
            self.cookie = response.cookies.get('session')
            try:
                # ensure the response is JSON encoded
                # jsonrpc_response = json.loads(response.text)
                jsonrpc_response = response.json()
            except:
                return None
            else:
                try:
                    result = reduce(operator.getitem, self.result_path, jsonrpc_response)
                except KeyError:
                    return 'Error return:{}\nrequest:{}'.format(jsonrpc_response, self.json_request)
                else:
                    return result
        except requests.HTTPError as e:
            raise NetMikoRequestsHTTPException("Error at Requesting: {}".format(e))
