import os
import pynetbox
from netmiko import ConnectHandler


def get_devices_by_site(site):
    netbox = pynetbox.api(os.getenv('APP_NETBOX_URL'), token=os.getenv('APP_NETBOX_TOKEN'))
    devices = netbox.dcim.devices.filter(site=site, manufacturer='cisco')
    return devices

def create_or_update_vlan_on_device(ip, vlan_id, vlan_name):
    device = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': os.getenv('APP_CISCO_USER'),
        'password': os.getenv('APP_CISCO_PASS'),
    }

    with ConnectHandler(**device) as net_connect:
        config_commands = [
            f'vlan {vlan_id}',
            f'name {vlan_name}',
            'exit',
            'wr mem'
        ]
        net_connect.send_config_set(config_commands)
        print(f"VLAN {vlan_id} ({vlan_name}) created/updated successfully on device {ip}")


def delete_vlan_on_device(ip, vlan_id):
    protected_vlans = [1, 999]

    if vlan_id in protected_vlans:
        print(f"VLAN {vlan_id} is protected on device {ip}")
        return

    if vlan_id not in protected_vlans:

        device = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': os.getenv('APP_CISCO_USER'),
            'password': os.getenv('APP_CISCO_PASS'),
        }

        with ConnectHandler(**device) as net_connect:
            config_commands = [
                f'no vlan {vlan_id}',
                'exit',
                'wr mem'
            ]
            net_connect.send_config_set(config_commands)
            print(f"VLAN {vlan_id} deleted successfully on device {ip}")
