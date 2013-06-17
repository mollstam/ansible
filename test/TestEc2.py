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
    mocked_instance = Mock(spec_set=params.keys())
    mocked_instance.configure_mock(**params)
    return mocked_instance

def instance_fulfilling_request(request):
    mock_group = Mock(name='Group');
    mock_group.id = request['group_id']
    mock_group.name = request['group_name']
    mock_region = Mock(name='RegionInfo');
    mock_region.name = request['region'];
    instance = mocked_instance({
        'key_name': request['key_name'],
        'groups' : [mock_group],
        'region': mock_region,
        'placement': request['zone'],
        'instance_type': request['instance_type'],
        'image_id': request['image'],
        'monitoring_state': 'enabled',
        'kernel': request['kernel'],
        'ramdisk': request['ramdisk'],
        'tags': request['instance_tags'],
    })

    return instance

class TestEc2IdempotentHandler(unittest.TestCase):

    def setUp(self):
        self.boto_mock = Mock()
        self.ec2_mock = Mock()
        self.boto_mock.ec2.connect_ec2.return_value = self.ec2_mock
        ec2_module_scope['boto'] = self.boto_mock

        request = {
            'key_name': 'test_key_name',
            'group_name': 'test_group_name',
            'group_id': 'sg-test',
            'region': 'test-1',
            'zone': 'test-1a',
            'instance_type': 'm1.test',
            'image': 'ami-test',
            'monitoring': True,
            'kernel': 'aki-test',
            'ramdisk': '-',
            'instance_tags': {'test-tag-key': 'test-tag-value'},
        }
        self.ec2_handler = ec2_module_scope['Ec2IdempotentHandler'](
            ec2_module_scope['boto'].ec2.connect_ec2(), request)

    def assertNotFulfilRequest(self, instance):
        self.assertEqual(self.ec2_handler.fulfils_request(instance),
                         False,
                         'should not fulfil')

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

    def test_instance_fulfils_request_true(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)

        assert self.ec2_handler.fulfils_request(instance), 'should fulfil'

    def test_instance_fulfils_request_different_key_name(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.key_name = 'another_key_name'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_group_name(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.groups[0].name = 'another_group_name'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_group_id(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.groups[0].id = 'another_group_id'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_region(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.region.name = 'another-1'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_zone(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.placement = 'another-1b'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_instance_type(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.instance_type = 'm1.xanother2'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_image(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.image_id = 'ami-another'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_monitoring(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.monitoring_state = 'disabled'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_kernel(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.kernel = 'aki-another'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_ramdisk(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.ramdisk = 'r-another'
        self.assertNotFulfilRequest(instance)

    def test_instance_fulfils_request_different_tags(self):
        instance = instance_fulfilling_request(self.ec2_handler.request)
        instance.tags = {'Name': 'Another Name'}
        self.assertNotFulfilRequest(instance)
