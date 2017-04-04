from __future__ import unicode_literals

from netmiko.json_connection import JsonConnection


class ExtremeExosJson(JsonConnection):
    """Extreme EXOS JSON RPC support."""
    def construct_params(self):
        self.set_url(url='http://{ip}:{port}/jsonrpc'.format(ip=self.host, port=self.port))
        self.set_json_request(request={
            'jsonrpc': '2.0',
            'method': 'cli',
            'params': None,
            'id': self.jsonrpc_id
        })
