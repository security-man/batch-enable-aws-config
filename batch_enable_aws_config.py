import boto3
import os
import logging
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

def enable_config(profile,account_id,region,config_name,bucket_prefix):
    iam_client = create_client('iam',profile,region)
    try:
        config_role = iam_client.create_service_linked_role(AWSServiceName="config.amazonaws.com")
    except ClientError:
        logging.exception("Couldn't create config.amazonaws.com role, role already exists.")
        print("")
        config_role = iam_client.get_role(RoleName="AWSServiceRoleForConfig")
    s3_client = create_client('s3',profile,region)
    try:
        s3_client.create_bucket(
            ACL='private',
            Bucket=(bucket_prefix + account_id),
            CreateBucketConfiguration={
                'LocationConstraint':region
            })
    except ClientError:
        logging.exception("Couldn't create S3 bucket, bucket already exists.")
        print("")
    config_client = create_client('config',profile,region)
    try:
        config_client.put_configuration_recorder(
            ConfigurationRecorder={
                'name': config_name,
                'roleARN': config_role['Role']['Arn'],
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
    except ClientError:
        logging.exception("Couldn't create config recorder, config recorder already exists in this account.")
        print("")
    try:
        config_client.put_delivery_channel(
            DeliveryChannel={
                'name': config_name,
                's3BucketName': bucket_prefix + account_id,
                'configSnapshotDeliveryProperties': {
                    'deliveryFrequency': 'Twelve_Hours'
                }
            }
        )
        config_client.start_configuration_recorder(ConfigurationRecorderName=config_name)
    except ClientError:
        logging.exception("Couldn't create config delivery channe;, config delivery channel already exists in this account.")
        print("")

def main():
    profiles = get_profiles()
    region = get_region()
    config_name = input('Enter name for config recorder. (hit Enter for default name "default")')
    if config_name == '':
        config_name == "default"
    bucket_prefix = input('Enter name for S3 config delivery bucket prefix. (hit Enter for default name "config-bucket-")')
    if bucket_prefix == '':
        bucket_prefix = "config-bucket-"
    for profile in profiles:
        account_id = profile.split('-')[0]
        enable_config(profile,account_id,region,config_name,bucket_prefix)

main()