import boto3
import os
import logging
import sys
from botocore.exceptions import ClientError

def get_profiles():
    # takes user input in the form of a comma-separated list of account ids
    accounts = input('Enter comma-separated Account IDs: ')
    accounts = accounts.split(',')
    # opens local aws cli config file to read aws profiles available
    f = open(os.path.expanduser('~/.aws/config'),'r')
    file_lines = f.readlines()
    profile_list = []

    # iterates through user-supplied aws account ids to find the matching aws profile and Admin role
    for line in file_lines:
        line_contents = line.split()
        if len(line_contents) > 0:
            if line_contents[0] == '[profile':
                profile_name = line_contents[1].split(']')
                for account in accounts:
                    if ((profile_name[0].split('-'))[0] == account):
                        if((profile_name[0].split('-'))[1] == "Admin"):
                            profile_list.append(profile_name[0])
                            accounts.remove(account)
    f.close()
    for profile in profile_list:
        logging.info("Added profile %s.", profile)
    return profile_list

def get_region():
    # user-input region to run script in
    script_region = input('Enter AWS region to run script in (hit Enter for default eu-west-2): ')
    if script_region == '':
        script_region = "eu-west-2"
    return script_region

def create_client(service,profile,region):
    session = boto3.Session(profile_name=profile,region_name=region)
    client = session.client(service)
    return client
    # creates an aws client for a particular service and profile

def set_config(profile,region):
    config_client = create_client('config',profile,region)
    try:
        current_config_name = config_client.list_configuration_recorders()['ConfigurationRecorderSummaries'][0]['name']
        current_config_recorder = config_client.describe_configuration_recorders(ConfigurationRecorderNames=[current_config_name])
        current_config_role = current_config_recorder['ConfigurationRecorders'][0]['roleARN']
        change_configuration = config_client.put_configuration_recorder(
            ConfigurationRecorder={
                'name': current_config_name,
                'roleARN': current_config_role,
                'recordingGroup': {
                    'allSupported': True,
                    'includeGlobalResourceTypes': True,
                    'resourceTypes': [],
                    'exclusionByResourceTypes': {
                        'resourceTypes': []
                    },
                    'recordingStrategy': {
                        'useOnly': 'ALL_SUPPORTED_RESOURCE_TYPES'
                    }
                },
                'recordingMode': {
                    'recordingFrequency': 'CONTINUOUS',
                    'recordingModeOverrides': [
                    ]
                }
            }
        )
        print(change_configuration)
    except ClientError as e:
        print(e)

profile = sys.argv[1]
region = sys.argv[2]

set_config(profile,region)