import configparser
import boto3
import time
import requests
import re 
import json

#Function to create a resource for ec2: 
def resource_ec2(aws_access_key_id, aws_secret_access_key, aws_session_token):
    ec2_serviceresource =  boto3.resource('ec2',
                       'us-east-1',
                       aws_access_key_id= aws_access_key_id,
                       aws_secret_access_key=aws_secret_access_key ,
                      aws_session_token= aws_session_token) 
    
    return(ec2_serviceresource)

#Function to create a client for ec2:
def client_ec2(aws_access_key_id, aws_secret_access_key, aws_session_token):
    ec2_serviceclient =  boto3.client('ec2',
                       'us-east-1',
                       aws_access_key_id= aws_access_key_id,
                       aws_secret_access_key=aws_secret_access_key ,
                      aws_session_token= aws_session_token) 
   
    
    return(ec2_serviceclient)

#Function to create and check a KeyPair : 
def create_keypair(key_pair_name, client):
    try:
        keypair = client.create_key_pair(KeyName=key_pair_name)
        print(keypair['KeyMaterial'])
        with open('lab1_keypair.pem', 'w') as f:
            f.write(keypair['KeyMaterial'])
        return(key_pair_name)

    except:
        print("\n\n============> Warning :  Keypair already created !!!!!!!<==================\n\n")
        return(key_pair_name)


# Function to create security group if it's not created already:
def create_security_group(Description,Groupe_name,vpc_id,resource, ip_address):
    Security_group_ID=resource.create_security_group(
        Description=Description,
        GroupName=Groupe_name,
        VpcId=vpc_id).id
    Security_group=resource.SecurityGroup(Security_group_ID)
    Security_group.authorize_ingress(
         IpPermissions=[
            {'FromPort':22,
             'ToPort':22,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':ip_address}]
            },
            {'FromPort':80,
             'ToPort':80,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':ip_address}]
            },
            {'FromPort':5000,
             'ToPort':5000,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':ip_address}]
            },
            {'FromPort':5001,
             'ToPort':5001,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':ip_address}]
            }
            ]
    ) 
    return Security_group_ID

#Function to create ec2 instances :
def create_instance_ec2(num_instances,ami_id,
    instance_type,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons,instance_function,user_data):
    instances=[]
    for i in range(num_instances):
        instance=ec2_serviceresource.create_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_pair_name,
            MinCount=1,
            MaxCount=1,
            Placement={'AvailabilityZone':Availabilityzons[i]},
            SecurityGroupIds=[security_group_id] if security_group_id else [],
            UserData=user_data,
            TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'lab2-'+str(instance_function)+"-"+str(i + 1)
                            },
                        ]
                    },
                ]
        )
        #Wait until the instance is running to get its public_ip adress
        instance[0].wait_until_running()
        instance[0].reload()
        #Get the public ip address of the instance and add it in the return
        public_ip = instance[0].public_ip_address
        instances.append([instance[0].id,public_ip])
        print ('Instance: '+str(instance_function)+str(i+1),' having the Id: ',instance[0].id,'and having the ip',public_ip,' in Availability Zone: ', Availabilityzons[i], 'is created')
    return instances
