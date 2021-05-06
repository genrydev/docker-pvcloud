# !/usr/bin/python
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import math
from lxml import etree
from pyvcloud.vcd.vm import VM
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.client import E
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.client import E_OVF
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import RelationType
from ansible.module_utils.vcd import VcdAnsibleModule
from pyvcloud.vcd.exceptions import EntityNotFoundException, OperationNotSupportedException


def disk_argument_spec():
  return dict(
    user=dict(type='str', required=False),
    password=dict(type='str', required=False),
    org=dict(type='str', required=False),
    host=dict(type='str', required=False),
    api_version=dict(type='str', required=False),
    verify_ssl_certs=dict(type='bool', required=False, default=False),

    vapp=dict(type='str', required=True),
    vm=dict(type='str', required=True),
    vdc=dict(type='str', required=True),
    disks=dict(type='list', required=True),
  )


class KhVcdVm(VcdAnsibleModule):
  def __init__(self, **kwargs):
    super(KhVcdVm, self).__init__(**kwargs)
    vapp_resource = self.get_target_resource()
    self.vapp = VApp(self.client, resource=vapp_resource)

  def get_target_resource(self):
    target_vapp = self.params.get('vapp')
    target_vdc = self.params.get('vdc')
    org_resource = Org(self.client, resource=self.client.get_org())
    target_vapp_resource = None
    target_vdc_resource = VDC(self.client, resource=org_resource.get_vdc(target_vdc))
    target_vapp_resource = target_vdc_resource.get_vapp(target_vapp)
    return target_vapp_resource

  def get_vm(self):
    vapp_vm_resource = self.vapp.get_vm(self.params.get('vm'))

    return VM(self.client, resource=vapp_vm_resource)

  def update_disk(self):
    response = dict()
    response['changed'] = False
    response['msg'] = list()

    disks = self.params.get('disks')
    disk_names = [disk.get("name") for disk in disks]
    disk_sizes = [disk.get("size", None) for disk in disks]
    disk_sizes = list(filter(lambda size: size is not None, disk_sizes))
    disk_old_sizes = [disk.get("origin_size", None) for disk in disks]
    disk_old_sizes = list(filter(lambda size: size is not None, disk_old_sizes))
    assert len(disk_sizes) == len(disk_names)
    size_after = ""
    size_before = ""
    vm = self.get_vm()
    vm_disks = self.client.get_resource(vm.resource.get('href') + '/virtualHardwareSection/disks')
    success = False
    for index, disk_name in enumerate(disk_names):
      for vm_disk_index, disk in enumerate(vm_disks.Item):
        disk_size = int(disk_sizes[index])
        #if disk['{' + NSMAP['rasd'] + '}ElementName'] == disk_name:
        #  response['msg'].append(disk['{' + NSMAP['rasd'] + '}ElementName'] + " == " + disk_name)
        #  response['msg'].append(str( int (int(disk['{' + NSMAP['rasd'] + '}VirtualQuantity'])  / 1024 / 1024)) + " == " + str(disk_old_sizes[index]) )
        
        if (disk['{' + NSMAP['rasd'] + '}ElementName'] == disk_name) and ( int( int(disk['{' + NSMAP['rasd'] + '}VirtualQuantity'])  / 1024 / 1024) == int(disk_old_sizes[index])):
          #response['msg'].append(str(int( int(disk['{' + NSMAP['rasd'] + '}VirtualQuantity'])  / 1024 / 1024)) + " - " + str(disk_old_sizes[index]))
          size_before = int( int(disk['{' + NSMAP['rasd'] + '}VirtualQuantity'])  / 1024 / 1024 / 1024)
          quantity = int(disk['{' + NSMAP['rasd'] + '}VirtualQuantity']) + int(disk_size * 1024 * 1024)
          capacity = int(quantity / 1024 /1024)
          disk['{' + NSMAP['rasd'] + '}VirtualQuantity'] = int(quantity)
          disk['{' + NSMAP['rasd'] + '}HostResource'].set('{' + NSMAP['vcloud'] + '}capacity', str(capacity))
          size_after = int(quantity / 1024 /1024 / 1024)
          #response['msg'].append(str(quantity))
          #response['msg'].append(str(capacity))
          #response['msg'].append(str(disk['{' + NSMAP['rasd'] + '}ElementName']))  
          success = True
        vm_disks.Item[vm_disk_index] = disk
    if success:
      update_disk_task = self.client.put_resource(vm.resource.get('href') + '/virtualHardwareSection/disks',vm_disks, EntityType.RASD_ITEMS_LIST.value)
      self.execute_task(update_disk_task)
      msg = '{0} increased from {1}G to {2}G.'
      response['msg'].append(msg.format(disk_name, size_before, size_after))
      response['changed'] = True
    else:
      msg = 'VM disk size not equal to {0}, nothing to do'
      response['msg'].append(msg.format(disk_name))
      response['msg'].append("You most make changes manually")
      response['changed'] = False
    return response
def main():
  argument_spec = disk_argument_spec()
  module = KhVcdVm(argument_spec=argument_spec, supports_check_mode=True)
  response = module.update_disk()
  module.exit_json(**response)


if __name__ == '__main__':
    main()
