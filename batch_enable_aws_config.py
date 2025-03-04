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
        logging.error("Couldn't create config.amazonaws.com role, role already exists.")
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
        logging.error("Couldn't create S3 bucket, bucket already exists.")
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
        logging.error("Couldn't create config recorder, config recorder already exists in this account.")
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
        logging.error("Couldn't create config delivery channe;, config delivery channel already exists in this account.")

def check_config_enabled(account_id):
    profile = account_id + '-RO'
    session = boto3.Session(profile_name = profile)
    config_client_eu_west_2 = session.client("config","eu-west-2")
    config_client_eu_west_1 = session.client("config","eu-west-1")
    try:
        status = 0
        delivery_channels_eu_west_2 = config_client_eu_west_2.describe_delivery_channels()
        delivery_channels_eu_west_1 = config_client_eu_west_1.describe_delivery_channels()
        if(len(delivery_channels_eu_west_2['DeliveryChannels']) < 1):
            status += 2
        if(len(delivery_channels_eu_west_1['DeliveryChannels']) < 1):
            status -= 1
    except ClientError as e:
        print(e)
    return status

def organisation_tidy(config_name,bucket_prefix):
    # establish client with root account (default profile)
    session = boto3.Session(profile_name="default")
    client = session.client('sts')
    org = session.client('organizations')

    # paginate through all org accounts
    paginator = org.get_paginator('list_accounts')
    page_iterator = paginator.paginate()

    # get accounts ids for active accounts
    account_ids = []
    print("Getting full list of accounts from AWS Organizations ...")
    for page in page_iterator:
        for account in page['Accounts']:
            if account['Status'] == 'ACTIVE':
                account_ids += {account['Id']}

    print("Account list populated!")
    print("")
    for account in account_ids:
        profile = account + "-Admin"
        status = check_config_enabled(account)
        if(status == 2):
            enable_config(profile,account,"eu-west-2",config_name,bucket_prefix)
            print("Config enabled for " + account + " region  = eu-west-2")
        elif(status == -1):
            enable_config(profile,account,"eu-west-1",config_name,bucket_prefix)
            print("Config enabled for " + account + " region  = eu-west-1")
        elif(status == 1):
            enable_config(profile,account,"eu-west-2",config_name,bucket_prefix)
            print("Config enabled for " + account + " region  = eu-west-2")
            enable_config(profile,account,"eu-west-1",config_name,bucket_prefix)
            print("Config enabled for " + account + " region  = eu-west-1")

def enable_specific_accounts():
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

organisation_tidy("default","config-bucket-")