from __future__ import print_function
from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.json_connection import JsonConnection


class CiscoNxosSSH(CiscoSSHConnection):
    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Nexus 5020 required extra delay post login
        """
        time.sleep(2)
        self.clear_buffer()
        self.set_base_prompt()
        self.disable_paging()

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text."""
        newline = re.compile(r'(\r\r\n|\r\n)')
        return newline.sub('\n', a_string).replace('\r', '')

class CiscoNxosJson(JsonConnection):
    """Cisco NX-API JSON RPC support."""
    def construct_params(self):
        self.set_url(url='http://{ip}:{port}/ins'.format(ip=self.host, port=self.port))
        self.set_json_request(request={
            'jsonrpc': '2.0',
            'method': 'cli',
            'params': {
                'cmd': None,
                'version': 1
            },
            'id': self.jsonrpc_id
        })
        self.set_result_path(path=['outputs', 'output', 'body'])