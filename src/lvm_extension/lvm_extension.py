##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.extension import ModelExtension, ViewError
from litp.core.model_type import ItemType, Collection, Property, PropertyType
from litp.core.model_type import View


class LvmExtension(ModelExtension):
    """
    LITP LVM extension for configuration of LVM.
    """

    def define_property_types(self):

        property_types = []

        expr = '^(ext4|raw|swap)$'
        property_types.append(PropertyType('fs_type', regex=expr))

        expr = '^(swap|(/[a-zA-Z0-9_/-]*))$'
        property_types.append(PropertyType('fs_mount_point', regex=expr))

        expr = '^[1-9][0-9]{0,}[MGT]$'
        property_types.append(PropertyType('fs_size', regex=expr))

        expr = r'^[\d{1,2}|100]$'
        property_types.append(PropertyType('snap_size', regex=expr))

        expr = '^[^,-]+$'
        property_types.append(PropertyType('disk_id', regex=expr))

        expr = '^([a-zA-Z0-9_/][a-zA-Z0-9_/-]*)$'
        property_types.append(PropertyType('vol_group', regex=expr))

        expr = '^(lvm|vxvm)$'
        property_types.append(PropertyType('vol_driver', regex=expr))

        return property_types

    def define_item_types(self):

        # Properties
        type_prop = Property('fs_type',
            prop_description='File System Type.',
            required=True,
            default='ext4')

        mount_prop = Property('fs_mount_point',
            prop_description='File System Mount Point.',
            required=True)

        size_prop = Property('fs_size',
            prop_description='File System Size.',
            required=True)

        disk_prop = Property('disk_id',
            prop_description='Identifier of Physical-Device Item.',
            required=True)

        vg_prop = Property('vol_group',
            prop_description='Name of Volume Group Item.',
            required=True)

        driver_prop = Property(
            'vol_driver',
            prop_description='Logical volume managment driver.'
                             ' Must be one of ``vxvm`` and ``lvm``.',
            required=True,
            default='lvm'
            )

        # Item Types
        fs_itype = ItemType('file-system',
            item_description='A file system.',
            type=type_prop,
            size=size_prop,
            mount_point=mount_prop)

        pd_itype = ItemType('physical-device',
            item_description='A physical device.',
            device_name=disk_prop)

        vg_itype = ItemType('volume-group',
            item_description='A storage volume group.',
            volume_group_name=vg_prop,
            file_systems=Collection('file-system', min_count=1, max_count=5),
            physical_devices=Collection('physical-device',
                                        min_count=1, max_count=1),
            volume_driver=driver_prop)

        sp_itype = ItemType('storage-profile',
            item_description='A storage profile.',
            extend_item='storage-profile-base',
            volume_groups=Collection('volume-group', min_count=1, max_count=2),
            view_root_vg=View('basic_string', LvmExtension.cb_select_root_vg))

        item_types = [fs_itype, pd_itype, vg_itype, sp_itype]

        return item_types

    @staticmethod
    def cb_select_root_vg(plugin_api_context, query_item):
        root_vg_claimants = list()

        for vol_group in query_item.volume_groups:
            roots_in_vg = set()
            for fs in vol_group.file_systems:
                if '/' == fs.mount_point:
                    roots_in_vg.add(fs.item_id)

            if 1 < len(roots_in_vg):
                raise ViewError("Storage-profile {0} has a VG '{1}' with >1 FS"
                        " mounted on '/': {2}".format(
                            query_item.get_vpath(),
                            vol_group.volume_group_name,
                            ','.join(list(roots_in_vg))))
            elif 1 == len(roots_in_vg):
                root_vg_claimants.append(vol_group)

        if not root_vg_claimants:
            raise ViewError("Storage-profile {0} does not have a VG with a "\
                    "FS mounted on '/'".format(query_item.get_vpath()))

        if 1 < len(root_vg_claimants):
            raise ViewError("Storage-profile {0} has >1 VG with a "\
                    "FS mounted on '/': {1}".format(
                        query_item.get_vpath(),
                        ','.join([vg.volume_group_name for vg in \
                                root_vg_claimants])))

        return root_vg_claimants[0].volume_group_name
