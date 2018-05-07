import subprocess

import boto3

REGION_NAME = 'us-west-2'
FUNCTION_NAME = 'doorcode'

if __name__ == '__main__':
    subprocess.check_call(['zip', '-r9', 'doorcode', '*'])

    session = boto3.Session(profile_name='doorcode')

    lambda_client = session.client('lambda', region_name=REGION_NAME)
    lambda_client.update_function_code(
        FunctionName=FUNCTION_NAME,
        Publish=True,
        ZipFile=open('doorcode.zip').read()
    )
