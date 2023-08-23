import os
import boto3
import time


stack_name = 'wordpress-hosting'

def stack_exists(event, cloudformation, stack_name):
    region = event['region']
    try:
        cloudformation = boto3.client('cloudformation', region_name=region)
        #check if stack exists based onstack name and region
        response = cloudformation.describe_stacks(StackName=stack_name) 
        return True
    except cloudformation.exceptions.ClientError as e:
        if 'Stack with id {0} does not exist'.format(stack_name) in str(e):
            return False
        else:
            raise
        


def lambda_handler(event, context):
    # Initialize the CloudFormation client
    
    region = event['region']
    domainName = event['domainName']
    containername = event['containername']
    # Define the stack parameters
    stack_parameters = [
        {
            'ParameterKey': 'DomainName',
            'ParameterValue': domainName
        },
        {
            'ParameterKey': 'Containername',
            'ParameterValue': containername
        }
       
        # Add more parameters as needed
    ]
    
    
    
    cloudformation = boto3.client('cloudformation', region_name=region)
    
    template_url =f"https://wordpressautomation.s3.amazonaws.com/masters/{region}.yaml"

    # Check if the stack already exists
    if not stack_exists(event, cloudformation, stack_name):
        # Create the stack
        response = cloudformation.create_stack(
            StackName=stack_name,
            TemplateURL=template_url,
            Parameters=stack_parameters,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        print("Stack creation initiated",response)
       
        #wait for stack to be created 
        waiter = cloudformation.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)
        print("Stack creation completed")
    else: 
        response = cloudformation.update_stack(
            StackName=stack_name,
            TemplateURL=template_url,
            Parameters=stack_parameters,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        print("Stack update initiated",response)
        
    #wait for stack to be updated
        waiter = cloudformation.get_waiter('stack_update_complete')
        waiter.wait(StackName=stack_name)
        print("Stack update completed")
    
    lambda_function = 'wordpressautomation'
    # Initialize the CloudFormation client
    lambda_client = boto3.client('lambda', region_name=region)
    response = lambda_client.invoke(FunctionName=lambda_function)
    print("Lambda function invoked",response)
    
#after stack creation is completed, write a function to trigger the lambda function that was created in the stack

  