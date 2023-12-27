import configparser
import boto3
from Setup_functions import *
import base64
import os
import json
from threading import Thread
import re

if __name__ == '__main__':
    # Get credentials from the config file :
    path = os.path.dirname(os.getcwd())
    config_object = configparser.ConfigParser()
    with open(path+"/credentials.ini","r") as file_object:
        #Loading of the aws tokens
        config_object.read_file(file_object)
        key_id = config_object.get("resource","aws_access_key_id")
        access_key = config_object.get("resource","aws_secret_access_key")
        session_token = config_object.get("resource","aws_session_token")
        ami_id = config_object.get("ami","ami_id")


    print('============================>SETUP Begins')

    #--------------------------------------Creating ec2 resource and client ----------------------------------------
    
    #Create ec2 resource with our credentials:
    ec2_serviceresource = resource_ec2(key_id, access_key, session_token)
    print("============> ec2 resource creation has been made succesfuly!!!!<=================")
    #Create ec2 client with our credentials:
    ec2_serviceclient = client_ec2(key_id, access_key, session_token)
    print("============> ec2 client creation has been made succesfuly!!!!<=================")

    #--------------------------------------Creating a keypair, or check if it already exists-----------------------------------
    
    key_pair_name = create_keypair('lab1_keypair', ec2_serviceclient)

    #---------------------------------------------------Get default VPC ID-----------------------------------------------------
    #Get default vpc description : 
    default_vpc = ec2_serviceclient.describe_vpcs(
        Filters=[
            {'Name':'isDefault',
             'Values':['true']},
        ]
    )
    default_vpc_desc = default_vpc.get("Vpcs")
   
    # Get default vpc id : 
    vpc_id = default_vpc_desc[0].get('VpcId')


    #--------------------------------------Try create a security group with all traffic inbouded--------------------------------
  
    try:
        security_group_id = create_security_group("All traffic sec_group","lab1_security_group",vpc_id,ec2_serviceresource)  
    
    except :
        #Get the standard security group from the default VPC :
        sg_dict = ec2_serviceclient.describe_security_groups(Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },

        {
                'Name': 'group-name',
                'Values': [
                    "lab1_security_group",
                ]
            },

        ])

        security_group_id = (sg_dict.get("SecurityGroups")[0]).get("GroupId")
    

    #--------------------------------------Pass flask deployment script into the user_data parameter ------------------------------
    with open('flask_orchestrator.sh', 'r') as f :
        flask_script_orchestrator = f.read()

    ud_orchestrator = str(flask_script_orchestrator)

    with open('flask_workers.sh', 'r') as f :
        flask_script_worker = f.read()

    ud_workers = str(flask_script_worker)
    ud_orchestrator=''

    #--------------------------------------Create Instances of orchestrator and workers ------------------------------------------------------------

    # Create 4 intances with m4.large as workers:
    Availabilityzons_Cluster1=['us-east-1a','us-east-1b','us-east-1a','us-east-1b','us-east-1a']
    instance_type = "m4.large"
    print("\n Creating instances : the workers ")

    # Creation of the 4 workers
    workers_m4= create_instance_ec2(4,ami_id, instance_type,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons_Cluster1,"worker",ud_workers)

    #Update test.json with the new workers ip
    update_test_json(workers_m4)
    
    time.sleep(330)
    print('\n Waiting for deployement of flask application on workers containers ....\n')
    
    #Modify the flask_orchestrator.sh file with the new containers ip
    update_orchestrator_sh(ud_orchestrator)

    print("\n Creating instances : Orchestrator ")

    # Creation of the orchestrator
    orchestrator_m4=create_instance_ec2(1,ami_id, instance_type,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons_Cluster1,"orchestrator",ud_orchestrator)

    print("\n Orchestrator and the 4 workers created successfully")
    
    print('============================>SETUP ends')

