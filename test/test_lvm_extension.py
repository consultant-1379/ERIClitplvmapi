##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import unittest
import os.path

from litp.core.plugin_manager import PluginManager
from litp.core.model_manager import ModelManager
from litp.core.plugin_context_api import PluginApiContext
from litp.extensions.core_extension import CoreExtension
from litp.core.execution_manager import ExecutionManager
from lvm_extension.lvm_extension import LvmExtension

from litp.core.validators import ValidationError
from litp.core.extension import ViewError

class TestLvmExtension(unittest.TestCase):
    def setUp(self):
        self.model_manager = ModelManager()
        self.plugin_manager = PluginManager(self.model_manager)
        self.context = PluginApiContext(self.model_manager)

        core_ext = CoreExtension()
        self.lvm_ext = LvmExtension()

        self.prop_types = dict()
        for prop_type in self.lvm_ext.define_property_types():
            self.prop_types[prop_type.property_type_id] = prop_type

        for ext in [core_ext, self.lvm_ext]:
            self.plugin_manager.add_property_types(ext.define_property_types())
            self.plugin_manager.add_item_types(ext.define_item_types())
            if ext == core_ext:
                self.plugin_manager.add_default_model()

    def tearDown(self):
        pass

    def test_valid_fs_type(self):
        self.assertTrue('fs_type' in self.prop_types)
        type_pt = self.prop_types['fs_type']

        bad_value_return = type_pt.run_property_type_validators('type', 'foo')
        self.assertEquals(1, len(bad_value_return))
        self.assertEquals('RegexError', bad_value_return[0].error_type)

        self.assertEquals([], type_pt.run_property_type_validators('type',
            'ext4'))
        self.assertEquals([], type_pt.run_property_type_validators('type',
            'swap'))
        self.assertEquals([], type_pt.run_property_type_validators('type',
            'raw'))

    def test_valid_mount_point(self):
        self.assertTrue('fs_mount_point' in self.prop_types)
        mountpoint_pt = self.prop_types['fs_mount_point']

        bad_value_return = mountpoint_pt.run_property_type_validators('mount_point', 'foo')
        self.assertEquals(1, len(bad_value_return))
        self.assertEquals('RegexError', bad_value_return[0].error_type)

        self.assertEquals([], mountpoint_pt.run_property_type_validators('mount_point', 'swap'))
        self.assertEquals([], mountpoint_pt.run_property_type_validators('mount_point', '/'))
        self.assertEquals([], mountpoint_pt.run_property_type_validators('mount_point', '//'))
        self.assertEquals([], mountpoint_pt.run_property_type_validators('mount_point', '/var/'))
        self.assertEquals([], mountpoint_pt.run_property_type_validators('mount_point', '/var/foo'))

    def test_valid_driver(self):
        self.assertTrue('vol_driver' in self.prop_types)
        driver_pt = self.prop_types['vol_driver']

        bad_value_return = driver_pt.run_property_type_validators('volume_driver', 'foo')
        self.assertEquals(1, len(bad_value_return))
        self.assertEquals('RegexError', bad_value_return[0].error_type)

        self.assertEquals([], driver_pt.run_property_type_validators('volume_driver', 'lvm'))
        self.assertEquals([], driver_pt.run_property_type_validators('volume_driver', 'vxvm'))

    def _create_mock_profiles(self):
        self.model_manager.create_core_root_items()
        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/1_vg_1_root_fs',
                storage_profile_name='1_vg_1_root')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/1_vg_1_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='alpha')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/1_vg_0_root_fs',
                storage_profile_name='1_vg_0_root')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/1_vg_0_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='a')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_0_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/home', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_0_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/1_vg_2_root_fs',
                storage_profile_name='1_vg_2_roots')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/1_vg_2_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='a')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_2_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_2_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs',
                storage_profile_name='2_vgs_0_root')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='alpha')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/opt', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/ovg',
                volume_group_name='bravo')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_A',
                mount_point='/usr', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_B',
                mount_point='/tmp', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs',
                storage_profile_name='2_vgs_1_root')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='alpha')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/opt', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/ovg',
                volume_group_name='bravo')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_A',
                mount_point='/usr', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_B',
                mount_point='/', size='12G')


        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs',
                storage_profile_name='2_vgs_2_roots')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='alpha')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/ovg',
                volume_group_name='bravo')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_A',
                mount_point='/usr', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_B',
                mount_point='/', size='12G')

    def test_root_vg_view_single_vg_no_root(self):
        self._create_mock_profiles()
        sp_qi = self.model_manager.query('storage-profile',
                storage_profile_name='1_vg_0_root')[0]
        try:
            getattr(sp_qi, 'view_root_vg')
        except ViewError as ve:
            self.assertEquals('Storage-profile /infrastructure/storage/'\
                    'storage_profiles/1_vg_0_root_fs does not have a VG with '\
                    'a FS mounted on \'/\'', str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_root_vg_view_single_vg_single_root(self):
        self._create_mock_profiles()
        sp_qi = self.model_manager.query('storage-profile',
                storage_profile_name='1_vg_1_root')[0]
        self.assertEquals('alpha', sp_qi.view_root_vg)

    def test_root_vg_view_single_vg_two_roots(self):
        self._create_mock_profiles()
        sp_qi = self.model_manager.query('storage-profile',
                storage_profile_name='1_vg_2_roots')[0]
        try:
            getattr(sp_qi, 'view_root_vg')
        except ViewError as ve:
            self.assertEquals('Storage-profile /infrastructure/storage/'\
                    'storage_profiles/1_vg_2_root_fs has a VG \'a\' with >1 '\
                    'FS mounted on \'/\': fs_A,fs_B', str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_root_vg_view_two_vgs_no_root(self):
        self._create_mock_profiles()
        sp_qi = self.model_manager.query('storage-profile',
                storage_profile_name='2_vgs_0_root')[0]
        try:
            getattr(sp_qi, 'view_root_vg')
        except ViewError as ve:
            self.assertEquals('Storage-profile /infrastructure/storage/'\
                    'storage_profiles/2_vgs_0_root_fs does not have a VG '\
                    'with a FS mounted on \'/\'', str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_root_vg_view_two_vgs_two_roots(self):
        self._create_mock_profiles()
        sp_qi = self.model_manager.query('storage-profile',
                storage_profile_name='2_vgs_2_roots')[0]
        try:
            getattr(sp_qi, 'view_root_vg')
        except ViewError as ve:
            self.assertEquals('Storage-profile /infrastructure/storage/'\
                    'storage_profiles/2_vgs_2_root_fs has >1 VG with a FS '\
                    'mounted on \'/\': alpha,bravo', str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_root_vg_view_two_vgs_single_root(self):
        self._create_mock_profiles()
        sp_qi = self.model_manager.query('storage-profile',
                storage_profile_name='2_vgs_1_root')[0]
        self.assertEquals('bravo', sp_qi.view_root_vg)
