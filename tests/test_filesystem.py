#!/usr/bin/env python

import mock
import os
from os import path
import sys
import unittest

from test_inventory import cleanup
from test_inventory import get_inventory
from test_inventory import make_config

INV_DIR = 'playbooks/inventory'
LIB_DIR = 'lib'

sys.path.append(path.join(os.getcwd(), LIB_DIR))
sys.path.append(path.join(os.getcwd(), INV_DIR))

import filesystem as fs

TARGET_DIR = path.join(os.getcwd(), 'tests', 'inventory')
USER_CONFIG_FILE = path.join(TARGET_DIR, 'openstack_user_config.yml')


def setUpModule():
    # The setUpModule function is used by the unittest framework.
    make_config()


def tearDownModule():
    # This file should only be removed after all tests are run,
    # thus it is excluded from cleanup.
    os.remove(USER_CONFIG_FILE)


class TestMultipleRuns(unittest.TestCase):
    def test_creating_backup_file(self):
        inventory_file_path = os.path.join(TARGET_DIR,
                                           'openstack_inventory.json')
        get_backup_name_path = 'filesystem._get_backup_name'
        backup_name = 'openstack_inventory.json-20160531_171804.json'

        tar_file = mock.MagicMock()
        tar_file.__enter__.return_value = tar_file

        # run make backup with faked tarfiles and date
        with mock.patch('filesystem.tarfile.open') as tar_open:
            tar_open.return_value = tar_file
            with mock.patch(get_backup_name_path) as backup_mock:
                backup_mock.return_value = backup_name
                fs._make_backup(TARGET_DIR, inventory_file_path)

        backup_path = path.join(TARGET_DIR, 'backup_openstack_inventory.tar')

        tar_open.assert_called_with(backup_path, 'a')

        # This chain is present because of how tarfile.open is called to
        # make a context manager inside the make_backup function.

        tar_file.add.assert_called_with(inventory_file_path,
                                        arcname=backup_name)

    def test_recreating_files(self):
        # Deleting the files after the first run should cause the files to be
        # completely remade
        get_inventory()

        get_inventory()

        backup_path = path.join(TARGET_DIR, 'backup_openstack_inventory.tar')

        self.assertFalse(os.path.exists(backup_path))

    def test_rereading_files(self):
        # Generate the initial inventory files
        get_inventory(clean=False)

        inv, path = fs.load_inventory(TARGET_DIR)
        self.assertIsInstance(inv, dict)
        self.assertIn('_meta', inv)
        # This test is basically just making sure we get more than
        # INVENTORY_SKEL populated, so we're not going to do deep testing
        self.assertIn('log_hosts', inv)

    def tearDown(self):
        # Clean up here since get_inventory will not do it by design in
        # this test.
        cleanup()


if __name__ == '__main__':
    unittest.main()
