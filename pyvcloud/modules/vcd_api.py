# !/usr/bin/python
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'knowhow'
}

DOCUMENTATION = '''
'''

EXAMPLES = '''
'''

RETURN = '''
'''

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import BasicLoginCredentials
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vcd_errors import VCDLoginError


#from pyvcloud.vcd.client import ApiVersion
#from pyvcloud.vcd.client import EdgeGatewayType
#from pyvcloud.vcd.client import GatewayBackingConfigType
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.gateway import Gateway

def disk_argument_spec():
  return dict(

    user=dict(type='str', required=False),
    password=dict(type='str', required=False),
    org=dict(type='str', required=False),
    host=dict(type='str', required=False),
    api_version=dict(type='str', required=False),
    vapp=dict(type='str', required=False),
    vm=dict(type='str', required=False),
    action=dict(type='str', required=True)
  )


class KhVCloudDirectorAPI(AnsibleModule):
  def __init__(self, **kwargs):
    super(KhVCloudDirectorAPI, self).__init__(**kwargs)
    self.login()

  def login(self):
    user = self.params.get('user')
    password = self.params.get('password')
    org = self.params.get('org')
    host = self.params.get('host')
    api_version = self.params.get('api_version')
    try:
      self.client = Client(host,api_version=api_version,verify_ssl_certs=False)
    except Exception as error:
      error = 'Error when create a client on host {} with api_version {}'
      raise VCDLoginError(error.format(host, api_version))
    try:
      self.client.set_credentials(BasicLoginCredentials(user, org, password))
    except Exception as error:
      error = 'Login failed for user {} to org {}'
      raise VCDLoginError(error.format(user, org))
  
  def manage_actions(self):
    action = self.params.get('action')
    if action == "org_info":
      return self.org_info()
    if action == "vm_info":
      return self.vm_info(name="")
    if action == "org_gateways":
      return self.org_gateways()

  def org_info(self):
    response = dict()
    response['changed'] = False
    response['json'] = list()
    ##
    org_details = dict()
    org_name = self.params.get('org')
    resource = self.client.get_org_by_name(org_name)
    org = Org(self.client, resource=resource)
    org_admin_resource = org.client.get_resource(org.href_admin)
    #org_details['token'] = str(self.client.get_xvcloud_authorization_token())
    org_details['href'] = str(org.href_admin)
    org_details['name'] = str(org_admin_resource['FullName'])
    org_details['description'] = str(org_admin_resource['Description'])
    org_details['enabled'] = str(org_admin_resource['IsEnabled'])
    org_details['users'] = list()
    org_details['vdcs'] = list()

    ## Users/UserReference
    for user in org_admin_resource['Users']['UserReference']:
      org_details['users'].append({
        'name': user.get('name'), 
        'href': user.get('href')
      })
    ## Vdcs/Vdc
    for vdc in org_admin_resource['Vdcs']['Vdc']:
      vdc_resources = self.client.get_resource(vdc.get('href'))
      ## ResourceEntities/ResourceEntity
      vapps = list()
      try:
        vdc_resources['ResourceEntities']['ResourceEntity']
      except AttributeError:
        vapps = list()
      else:
        for vapp in vdc_resources['ResourceEntities']['ResourceEntity']:
          if "vApp+" in vapp.get('type'):
            vapp_resourses = self.client.get_resource(vapp.get('href'))
            vms = list()
            try:
              vapp_resourses['Children']
            except AttributeError:
              vms = list()
            else:
              for vm in vapp_resourses['Children']['Vm']:
                vm_info = self.vm_info(name=vm.get('name'), vapp=vapp.get('name'))
                vms = vm_info['json']
              if len(vms) > 0:
                vapps.append({
                  'href': str(vapp.get('href')),
                  'name': str(vapp.get('name')),
                  'vms': vms
                })
      ## AvailableNetworks/Network
      nets = list()
      for net in vdc_resources['AvailableNetworks']['Network']:
        nets.append({
          'href': str(net.get('href')),
          'name': str(net.get('name'))
        })
      ## VdcStorageProfiles/VdcStorageProfile
      storages = list()
      
      for storage in vdc_resources['VdcStorageProfiles']['VdcStorageProfile']:
        storage_resources = self.client.get_resource(str(storage.get('href')))
        storages.append({
          'href': str(storage.get('href')),
          'name': str(storage.get('name')),
          'units': str(storage_resources['Units']),
          'total': str(storage_resources['Limit']),
          'used': str(storage_resources['StorageUsedMB']),
          'free': str(storage_resources['Limit'] - storage_resources['StorageUsedMB'])
        })

      vdc_name = vdc.get('name')
      vdc_resource = org.get_vdc(vdc_name)
      vdcenter = VDC(self.client, name=vdc_name, resource=vdc_resource)
      gateways = vdcenter.list_edge_gateways()

      org_details['vdcs'].append({
        'name': vdc.get('name'), 
        'href': vdc.get('href'),
        'cpu':{
          'units': str(vdc_resources['ComputeCapacity']['Cpu']['Units']),
          'total': str(vdc_resources['ComputeCapacity']['Cpu']['Limit']),
          'used': str(vdc_resources['ComputeCapacity']['Cpu']['Used']),
          'free': str(vdc_resources['ComputeCapacity']['Cpu']['Limit'] - vdc_resources['ComputeCapacity']['Cpu']['Used'])
        },
        'ram':{
          'units': str(vdc_resources['ComputeCapacity']['Memory']['Units']),
          'total': str(vdc_resources['ComputeCapacity']['Memory']['Limit']),
          'used': str(vdc_resources['ComputeCapacity']['Memory']['Used']),
          'free': str(vdc_resources['ComputeCapacity']['Memory']['Limit'] - vdc_resources['ComputeCapacity']['Memory']['Used'])
        },        
        'vapps': vapps,
        'networks': nets,
        'storages': storages,
        'gateways': gateways
      })
    ## Networks/Network
    ## Catalogs/CatalogReference
    response['json'] = org_details
    ##
    response['changed'] = True
    return response

  def _gateways(self, org_name, vdc_name):
    org_resource = self.client.get_org_by_name(org_name)
    org = Org(self.client, resource=org_resource)
    vdc_resource = org.get_vdc(vdc_name)
    vdc = VDC(self.client, name=vdc_name, resource=vdc_resource)
    gateways = vdc.list_edge_gateways()
    result = list()
    for gateway in gateways:
      nats = list()
      nat_resources = self.client.get_resource(str(gateway.get('href')))
      for nat in nat_resources['Configuration']['EdgeGatewayServiceConfiguration']['NatService']['NatRule']:
        if nat['IsEnabled'] == True:
          nats.append({
            'id': str(nat['Id']),
            'type': str(nat['RuleType']),
            'network': str(nat['GatewayNatRule']['Interface'].get('name')),
            'original': str(nat['GatewayNatRule']['OriginalIp']),
            'translated': str(nat['GatewayNatRule']['TranslatedIp'])
          })
      result.append({
        'href': gateway.get('href'),
        'name': gateway.get('name'),
        'nats': nats
      })
    return result

  def org_gateways(self):
    response = dict()
    response['changed'] = False
    response['json'] = list()
    ##
    org_details = dict()
    org_name = self.params.get('org')
    org_resource = self.client.get_org_by_name(org_name)
    org = Org(self.client, resource=org_resource)
    org_admin_resource = org.client.get_resource(org.href_admin)
    #org_details['token'] = str(self.client.get_xvcloud_authorization_token())
    org_details['href'] = str(org.href_admin)
    org_details['name'] = str(org_admin_resource['FullName'])
    org_details['description'] = str(org_admin_resource['Description'])
    org_details['enabled'] = str(org_admin_resource['IsEnabled'])
    org_details['gateways'] = list()

    for vdc in org_admin_resource['Vdcs']['Vdc']:
      gateways = self._gateways(org_name=str(org_admin_resource['FullName']), vdc_name=vdc.get('name'))
      for gateway in gateways:
        org_details['gateways'].append( gateway )
        
    response['json'] = org_details
    response['changed'] = True
    return response

  def vm_info(self, name="",vapp=""):
    response = dict()
    response['changed'] = False
    response['json'] = list()
    ##
    if name == "":
      name = self.params.get('vm')
    vm_details = dict()
    vm_query_resources = self.client.get_resource('https://' + self.params.get('host') + '/api/query?type=vm&filter=name==' + name)
    if int(vm_query_resources.get('total')) > 0:
      for vm_query_resource in vm_query_resources['VMRecord']:
        if vm_query_resource.get('isDeployed') != "false" and vm_query_resource.get('status') != "POWERED_OFF":
          vdc_resources = self.client.get_resource(str(vm_query_resource.get('vdc')))
          vm_resources = self.client.get_resource(str(vm_query_resource.get('href')))
          network_result = list()
          dnats = list()
          gateways = self._gateways(org_name=str(self.params.get('org')), vdc_name=vdc_resources.get('name'))
          
          ## NetworkConnectionSection/NetworkConnection
          for network in vm_resources['NetworkConnectionSection']['NetworkConnection']:
            try:
              str(network['IpAddress'])
            except AttributeError:
              ip_address = "DHCP"
            else:
              ip_address = str(network['IpAddress'])
              dnat_net = list()
              
              for gateway in gateways:
                for nat in gateway['nats']:
                  if nat['type'] == "DNAT" and str(nat['translated']) == ip_address:
                    # dnats.append({
                    #   'ip': ip_address,
                    #   'network': str(nat['network']),
                    #   'original': str(nat['translated']),
                    #   'translated': str(nat['original'])
                    # })
                    if str(nat['original']) not in dnats:
                     dnats.append(str(nat['original']))
                     dnat_net.append(str(nat['original']))
              network_result.append({
                'primary': str(network['NetworkConnectionIndex'] == vm_resources['NetworkConnectionSection']['PrimaryNetworkConnectionIndex']),
                'ip_address': ip_address,
                'connected': str(network['IsConnected']),
                'mac': str(network['MACAddress']),
                'mode': str(network['IpAddressAllocationMode']),
                'type': str(network['NetworkAdapterType']),
                'network_name': str(network.get('network')),
                'href': str(vm_resources['NetworkConnectionSection'].get('href')),
                'dnats': dnat_net
              })
          storage_result = dict()
          for storage in vdc_resources['VdcStorageProfiles']['VdcStorageProfile']:
            if storage.get('name') == vm_query_resource.get('storageProfileName'):
              storage_resources = self.client.get_resource(str(storage.get('href')))
              storage_result = {
                'name': storage.get('name'),
                'href': storage.get('href'),
                'units': str(storage_resources['Units']),
                'total': str(storage_resources['Limit']),
                'used': str(storage_resources['StorageUsedMB']),
                'free': str(storage_resources['Limit'] - storage_resources['StorageUsedMB'])
              }

          vm_details = {
            'vapp': {
              'name': str(vm_query_resource.get('containerName')),
              'href': str(vm_query_resource.get('container'))
            },
            #'token': str(self.client.get_xvcloud_authorization_token()),
            'name': str(vm_query_resource.get('name')),
            'href': str(vm_query_resource.get('href')),
            'hardware_version': str(vm_query_resource.get('hardwareVersion')),
            'ram': str(vm_query_resource.get('memoryMB')),
            'cpu': str(vm_query_resource.get('numberOfCpus')),
            'storage': storage_result,
            'vdc': {
              'name': vdc_resources.get('name'),
              'href': vdc_resources.get('href')
            },
            'capabilities': {
              'ram_hot_add': str(vm_resources['VmCapabilities']['MemoryHotAddEnabled']),
              'cpu_hot_add': str(vm_resources['VmCapabilities']['CpuHotAddEnabled']),
              'href': str(vm_resources['VmCapabilities'].get('href'))
            },
            'network': network_result,
            'dnats': dnats
          }
          if vapp == "":
            response['json'].append( vm_details )
          else:
            if str(vm_query_resource.get('name')) == name and str(vm_query_resource.get('containerName')) == vapp:
              response['json'].append( vm_details )
    else:
      raise Exception("No vm with name=" + name + " was found.")
    response['changed'] = True
    return response


def main():
  argument_spec = disk_argument_spec()
  module = KhVCloudDirectorAPI(argument_spec=argument_spec, supports_check_mode=True)
  response = dict(
    json=dict(type='str')
  )
  try:
    if module.params.get('action'):
      response = module.manage_actions()
    else:
      raise Exception('One of the state/operation should be provided.')
  except Exception as error:
    response['json'] = error
    response['changed'] = False
    module.fail_json(**response)
  module.exit_json(**response)

if __name__ == '__main__':
    main()
