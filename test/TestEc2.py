# -*- coding: utf-8 -*-

import unittest
import inspect, os, sys
import boto.ec2
import mock
from mock import MagicMock, Mock

# Setup an environment for ec2 module to run in, not the most testable code
mockedAnsibleModule = Mock()
mockedAnsibleModule.params = {
    'wait_timeout': 0,
    'count': 0,
}
mockedBoto = Mock()
ec2_module_scope = {
    'AnsibleModule': lambda *args, **kwargs: mockedAnsibleModule,
    'BOOLEANS': [False, True],
    'os': os,
}
for libdir in sys.path:
    path = os.path.join(libdir, 'cloud/ec2')
    if (os.path.isfile(path)):
        execfile(path, ec2_module_scope)
        break

class TestEc2Instance(unittest.TestCase):

    def test_class_loaded(self):
        try:
            ec2_module_scope['Ec2IdempotentHandler']
        except NameError:
            assert False == True, 'Ec2IdempotentHandler is not loaded'
