import configparser
import boto3
import time
import requests
import re 
import json

#Function to create a service resource for ec2: 
def resource_ec2(aws_access_key_id, aws_secret_access_key, aws_session_token):
    ec2_serviceresource =  boto3.resource('ec2',
                       'us-east-1',
                       aws_access_key_id= aws_access_key_id,
                       aws_secret_access_key=aws_secret_access_key ,
                      aws_session_token= aws_session_token) 
    
    return(ec2_serviceresource)

#Function to create a service client for ec2
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


#---------------------------------------------To re check----------------------------------------------
'Function to create a new vpc (Maybe no need for this, just use default vpc)'
def create_vpc(CidrBlock,resource):
   VPC_Id=resource.create_vpc(CidrBlock=CidrBlock).id
   return VPC_Id

'Function to create security group (Maybe no need for this, just use get securty group of default vpc)'
def create_security_group(Description,Groupe_name,vpc_id,resource):
    Security_group_ID=resource.create_security_group(
        Description=Description,
        GroupName=Groupe_name,
        VpcId=vpc_id).id
    
    Security_group=resource.SecurityGroup(Security_group_ID)
    
    #Add an inbounded allowing inbounded traffics of tcp protocol, and ports 22,80,5000,5001, and all Ipranges.  
    Security_group.authorize_ingress(
         IpPermissions=[
            {'FromPort':22,
             'ToPort':22,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            },
            {'FromPort':80,
             'ToPort':80,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            },
            {'FromPort':5000,
             'ToPort':5000,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            },
            {'FromPort':5001,
             'ToPort':5001,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            }
            ]
    ) 
    return Security_group_ID

#------------------------------------------------End----------------------------------------------------


#Function to create ec2 instances :  The function returns a list containing the [id of instance,public_ip_address]

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

#Function to automatically update the ip of the workers in the flask_orchestrator.sh file
def update_orchestrator_sh(ud_orchestrator):
    ##Once the test json is updated (with new ip), modify automatically the IP in orchestrator_user data 
    with open("test.json","r") as f:
            data=json.load(f)
    #get the modified IP
    new_ip=str(data)
    new_ip=new_ip.replace("'", '"')
    #Get the content of the old test.json content in the previous user id
    pattern = re.compile(r'test\.json\n(.*?)\nEOL', re.DOTALL)
    result = re.search(pattern, ud_orchestrator)
    old_ip = result.group(1)

    #Replace the content of the updated ip in the ud_orchestrator
    ud_orchestrator=ud_orchestrator.replace(old_ip,new_ip)
    #Rewrite the updated file 
    with open('flask_orchestrator.sh', 'w') as file:
        file.write(ud_orchestrator)
    return(print("\n Updated flask_orchestrator with the new containers ip "))

#Function to automatically update the ip of the workers in the test.json file
def update_test_json(workers_m4):
    # Modify the file test.json en fonction pour modifier les IP
    with open("test.json","r") as f:
            data=json.load(f)

    # Modify the ip in the test.json
    container_count = 0
    for i in range(len(workers_m4)):
        # Get one worker and map it to two containers with different ports :port 5000 and 5001
        for _ in range(2):
            container_count += 1
            container_id = "container" + str(container_count)
            data[container_id]["ip"]=workers_m4[i][1]
    with open ("test.json","w") as f:
        json.dump(data,f)
    
    return(print("\n\n json file updated successfully \n\n"))