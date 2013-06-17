# -*- coding: utf-8 -*-

import unittest
import inspect, os, sys
import boto.ec2
import mock
from mock import MagicMock, Mock

# Setup an environment for ec2 module to run in, not the most testable code
mocked_ansibleModule = Mock()
mocked_ansibleModule.params = {
    'wait_timeout': 0,
    'count': 0,
}
ec2_module_scope = {
    'AnsibleModule': lambda *args, **kwargs: mocked_ansibleModule,
    'BOOLEANS': [False, True],
    'os': os,
}
for libdir in sys.path:
    path = os.path.join(libdir, 'cloud/ec2')
    if (os.path.isfile(path)):
        execfile(path, ec2_module_scope)
        break

def mocked_instance(params):
    mocked_instance = Mock(name='mocked_instance')
    mocked_instance.params = params
    mocked_instance.tags = params['tags']
    return mocked_instance

class TestEc2IdempotentHandler(unittest.TestCase):

    def setUp(self):
        self.boto_mock = Mock()
        self.ec2_mock = Mock()
        self.boto_mock.ec2.connect_ec2.return_value = self.ec2_mock
        ec2_module_scope['boto'] = self.boto_mock

        self.ec2_handler = ec2_module_scope['Ec2IdempotentHandler'](
            ec2_module_scope['boto'].ec2.connect_ec2())

    def test_class_loaded(self):
        try:
            ec2_module_scope['Ec2IdempotentHandler']
        except NameError:
            assert False == True, 'Ec2IdempotentHandler is not loaded'

    def test_load_running_instances_by_ansible_id(self):
        expected_id = 'test_id'
        expected_instance = mocked_instance({
            'tags': {'Name': 'test_name',
                     'ansible_idempotency_id': 'test_id'}
        })
        self.ec2_mock.get_all_instances.return_value = [expected_instance]

        instances = self.ec2_handler.load_running_instances(expected_id)
        assert isinstance(instances, list), 'instances is not list'
        (self.ec2_mock.get_all_instances
            .assert_called_with(None, {'tag-key':'ansible_idempotency_id',
                                       'tag-value': expected_id}))
        self.assertEqual(instances[0], expected_instance)
