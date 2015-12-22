from arm_disk_manager import DiskManager
from auth_token import AuthToken
from twisted.trial import unittest
from eliot import Message, Logger
from bitmath import Byte, GiB
from twisted.trial.unittest import SkipTest
from azure.storage.blob import BlobService
from azure.mgmt.common import SubscriptionCloudCredentials
from azure.mgmt.resource import ResourceManagementClient
from vhd import Vhd
import os
import yaml
import socket

_logger = Logger()
azure_config = None
config_file_path = os.environ.get('AZURE_CONFIG_FILE')

if config_file_path is not None:
    config_file = open(config_file_path)
    config = yaml.load(config_file.read())
    azure_config = config['azure_settings']

class DiskCreateTestCase(unittest.TestCase):
    def test_create_blank_vhd(self):
        auth_token = AuthToken.get_token_from_client_credentials(
            azure_config['subscription_id'],
            azure_config['tenant_id'],
            azure_config['client_id'],
            azure_config['client_secret'])
        creds = SubscriptionCloudCredentials(azure_config['subscription_id'], auth_token)
        self._resource_client = ResourceManagementClient(creds)
        self._azure_storage_client = BlobService(
            azure_config['storage_account_name'],
            azure_config['storage_account_key'])

        manager = DiskManager(self._resource_client, 
          self._azure_storage_client,
          azure_config['storage_account_container'],
          azure_config['group_name'],
          azure_config['location'])

        link = manager.create_disk(azure_config['test_vhd_name'], 2)
        self.assertEqual(link , 'https://' + self._azure_storage_client.account_name + '.blob.core.windows.net/' + azure_config['storage_account_container'] + '/' + azure_config['test_vhd_name'] + '.vhd')
        disks = manager.list_disks()

        found = False
        for i in range(len(disks)):
          disk = disks[i]
          if disk.name == azure_config['test_vhd_name']:
            found = True
            break

        self.assertEqual(found, True, 'Expected disk: ' + azure_config['test_vhd_name'] + ' to be listed in DiskManager.list_disks')
        
        manager.destroy_disk(azure_config['test_vhd_name'])
        disks = manager.list_disks()
        found = False
        for i in range(len(disks)):
          disk = disks[i]
          if disk.name == azure_config['test_vhd_name']:
            found = True
            break

        self.assertEqual(found, False, 'Expected disk: ' + azure_config['test_vhd_name'] + ' not to be listed in DiskManager.list_disks')
        
    def test_attach_blank_vhd(self):
        auth_token = AuthToken.get_token_from_client_credentials(
            azure_config['subscription_id'],
            azure_config['tenant_id'],
            azure_config['client_id'],
            azure_config['client_secret'])
        creds = SubscriptionCloudCredentials(azure_config['subscription_id'], auth_token)
        self._resource_client = ResourceManagementClient(creds)

        
        creds = SubscriptionCloudCredentials(azure_config['subscription_id'], auth_token)
        self._resource_client = ResourceManagementClient(creds)
        self._azure_storage_client = BlobService(
            azure_config['storage_account_name'],
            azure_config['storage_account_key'])

        manager = DiskManager(self._resource_client, 
          self._azure_storage_client,
          azure_config['storage_account_name'],
          azure_config['group_name'],
          azure_config['location'])

        manager.create_disk(azure_config['test_vhd_name'], 2)
        # print "Attempting to attach disk: " + link
        node_name = azure_config['test_vm_name']
        manager.attach_disk(node_name, azure_config['test_vhd_name'], 2)

        disks = manager.list_attached_disks(node_name)
        found = False
        for i in range(len(disks)):
            disk = disks[i]
            if disk['name'] == azure_config['test_vhd_name']:
                found = True
                break

        self.assertEqual(found, True, 'Expected to find an attached disk: ' + azure_config['test_vhd_name'])
        manager.detach_disk(node_name, azure_config['test_vhd_name'])

        disks = manager.list_attached_disks(node_name)
        found = False
        for i in range(len(disks)):
            disk = disks[i]
            if disk['name'] == azure_config['test_vhd_name']:
                found = True
                break
        self.assertEqual(found, False, 'Expected disk: ' + azure_config['test_vhd_name'] + ' to not be attached');

        manager.destroy_disk(azure_config['test_vhd_name'])
        all_disks = manager.list_disks()
        found = False
        for i in range(len(all_disks)):
          disk = all_disks[i]
          if disk.name == azure_config['test_vhd_name']:
            found = True
            break

        self.assertEqual(found, False, 'Expected disk: ' + azure_config['test_vhd_name'] + ' not to be listed in DiskManager.list_disks')
