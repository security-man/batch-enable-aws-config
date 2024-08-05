# batch-enable-aws-config
Batch enable AWS Config with desired settings for either 1 account, a set of accounts, or an entire AWS Organisation.

## Pre-requisites
This python script relies on [auto-update-aws-config](https://github.com/security-man/auto-update-aws-config), which ISN'T to be confused with this repository. The [auto-update-aws-config](https://github.com/security-man/auto-update-aws-config) repository was poorly-named and refers to the .aws/config file used for AWS CLI access! The [auto-update-aws-config](https://github.com/security-man/auto-update-aws-config) project allows the .aws/config file to be automatically set using user-defined IAM role profiles for ALL AWS accounts within an AWS Organisation.

## Installation
Provided you have already run [auto-update-aws-config](https://github.com/security-man/auto-update-aws-config), simply copy the python 'batch_enable_aws_config.py' script to your local directory and execute!

```bash
python3 batch_enable_aws_config.py
```

## User Inputs
The script will prompt you for the following inputs:

- list of AWS Account IDs to enable AWS config for, separated by commas (e.g., "123456781234,123456781235,123456781236,...")
- region to enable config (default setting is "eu-west-2")
- config recorder name (default setting is "default")
- config S3 bucket name (default setting is "config-bucket-<AWSACCOUNTID>")

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[GNU GPLv3]
(https://choosealicense.com/licenses/gpl-3.0/)