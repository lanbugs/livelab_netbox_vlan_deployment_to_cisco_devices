import os
from rq import Queue
from rq.job import Job
from .worker import connection
from .backend import get_devices_by_site, create_or_update_vlan_on_device, delete_vlan_on_device
q = Queue(connection=connection, name=os.getenv('APP_QUEUE_NAME'))

def check_for_vlan_deployment_tag(data):
    """
    Check for VLAN Deployment Tag

    :param data: The data containing the VLAN deployment tags.
                  Must be a dictionary with 'tags' key containing a list of tags.
    :return: True if the VLAN deployment tag 'no_vlan_deployment' is found, False otherwise.
    """
    data = dict(data)
    if 'tags' in data and isinstance(data['tags'], list):
        for tag in data['tags']:
            if tag.get('slug') == 'no_vlan_deployment':
                return True
    return False

def task_enqueue_vlan_create(vlan_id, vlan_name, vlan_site):
    """
    :param vlan_id: The ID of the VLAN to be created.
    :param vlan_name: The name of the VLAN to be created.
    :param vlan_site: The site where the VLAN should be created.
    :return: None

    This method enqueues a job to create a VLAN on all devices in a given site. It first retrieves the devices in the site using the get_devices_by_site function. Then, it iterates over each device and checks if it has a primary IP address. If it does, it checks if the device has a VLAN deployment tag using the check_for_vlan_deployment_tag function. If the device does not have the tag, it extracts the IP address from the primary IP and creates a job to execute the task_device_vlan_create function with the IP, VLAN ID, and VLAN name as arguments. The created job is then enqueued using the q.enqueue_job method.

    Note: The connection object must be defined beforehand.
    """
    devices = get_devices_by_site(vlan_site)

    for device in devices:
        if device.primary_ip:
            if check_for_vlan_deployment_tag(device) is False:
                ip = str(device.primary_ip).split("/")[0]

                # enqueue job for device
                job = Job.create(
                    func=task_device_vlan_create,
                    args=(ip, vlan_id, vlan_name),
                    connection=connection
                )

                q.enqueue_job(job)


def task_enqueue_vlan_delete(vlan_id, vlan_site):
    """
    :param vlan_id: ID of the VLAN to be deleted.
    :param vlan_site: Site where the VLAN is located.
    :return: None

    Enqueues a job to delete a VLAN on all devices in the specified site.

    """
    devices = get_devices_by_site(vlan_site)

    for device in devices:
        if device.primary_ip:
            if check_for_vlan_deployment_tag(device) is False:
                ip = str(device.primary_ip).split("/")[0]

                # enqueue job for device
                job = Job.create(
                    func=task_device_vlan_delete,
                    args=(ip, vlan_id),
                    connection=connection
                )

                q.enqueue_job(job)


def task_device_vlan_create(ip, vlan_id, vlan_name):
    """
    Create a VLAN on a device.

    :param ip: The IP address of the device.
    :type ip: str
    :param vlan_id: The ID of the VLAN to be created.
    :type vlan_id: int
    :param vlan_name: The name of the VLAN to be created.
    :type vlan_name: str
    :return: None
    :rtype: None
    """
    create_or_update_vlan_on_device(ip, vlan_id, vlan_name)

def task_device_vlan_delete(ip, vlan_id):
    """
    :param ip: The IP address of the device where the VLAN will be deleted.
    :param vlan_id: The ID of the VLAN to be deleted.
    :return: None

    This method is used to delete a VLAN on a specific device. It takes the IP address of the device and the ID of the VLAN as parameters. The method internally calls the `create_vlan_on_device` function to delete the VLAN on the device.
    """
    delete_vlan_on_device(ip, vlan_id)