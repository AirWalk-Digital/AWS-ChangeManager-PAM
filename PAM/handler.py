from datetime import datetime, timedelta
import json

import boto3


def create_role(event, context):
    iam = boto3.client('iam')
    orgs = boto3.client("organizations")

    org = orgs.describe_organization()

    requestor_role = event['requestor_role']
    with open('PAMTrustPolicy.json','r') as fpolicy:
        trustpolicy = json.load(fpolicy)

    now = datetime.utcnow()
    from_time = datetime.strftime(now, '%Y-%m-%dT%H:%M:%SZ')
    to_time = datetime.strftime(now + timedelta(minutes=20), '%Y-%m-%dT%H:%M:%SZ')
    
    trustpolicy['Statement'][0]['Principal']['AWS'] = requestor_role
    trustpolicy['Statement'][1]['Principal']['AWS'] = requestor_role 
    
    trustpolicy['Statement'][0]['Condition']['StringEquals']['aws:PrincipalOrgID'] = org['Organization']['Id']

    trustpolicy['Statement'][0]['Condition']['DateGreaterThan']['aws:CurrentTime'] = from_time
    trustpolicy['Statement'][0]['Condition']['DateLessThan']['aws:CurrentTime'] = to_time
    
    
    role_name = f'PAM-Automation'
    role_exists = True
    try:
        response = iam.get_role(RoleName=role_name)
    except iam.exceptions.NoSuchEntityException:
        role_exists = False
    
    if role_exists:
        response = iam.update_assume_role_policy(
            RoleName=role_name,
            PolicyDocument=json.dumps(trustpolicy))
    else:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trustpolicy),
            MaxSessionDuration=3600)
    
        # The managed policy to attach to the role
        response = iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess')

    return {
        "message": f"{requestor_role} has been granted access to {role_name} until {to_time}",
    }