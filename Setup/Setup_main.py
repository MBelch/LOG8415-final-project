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
    
    key_pair_name = create_keypair('final_project_keypair', ec2_serviceclient)

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


    #--------------------------------------Try create a security group for the cluster traffic inbouded--------------------------------
    # We added the ip address of the proxy since it's the only instance that sends requests:
    try:
        security_group_id = create_security_group("Proxy traffic sec_group","security_group_cluster",vpc_id,ec2_serviceresource,"54.89.126.22")  
    
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
                    "security_group_cluster",
                ]
            },

        ])

        security_group_id = (sg_dict.get("SecurityGroups")[0]).get("GroupId")

    #-----------------------Try create a security group with traffic from gatekeeper-trusted host inbouded for proxy--------------------------------
    
    # Secrity group for the proxy :
    # The proxy is supposed to get the traffic only from the trusted host from the gatekeeper :
    try:
        pxy_sg_id = create_security_group("Gatekeeper traffic sec_group","security_group_pxy",vpc_id,ec2_serviceresource,"50.65.104.65")  
    
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
                    "security_group_pxy",
                ]
            },

        ])

        pxy_sg_id = (sg_dict.get("SecurityGroups")[0]).get("GroupId")
    
    #-----------------------Try create a security group with all traffic inbouded for Gatekeeper--------------------------------
    
    # Secrity group for the gatekeeper :
    # The gatekeeper is supposed to get all traffic and then it processed which one is a trusted host:
    try:
        gk_sg_id = create_security_group("All traffic sec_group","lab1_security_group",vpc_id,ec2_serviceresource,"0.0.0.0/0")  
    
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
                    "security_group_gk",
                ]
            },

        ])

        gk_sg_id = (sg_dict.get("SecurityGroups")[0]).get("GroupId")
    

    #--------------------------------------Pass flask deployment script into the user_data parameter ------------------------------
    with open('mysql_worker.sh', 'r') as f :
        script_worker = f.read()
    ud_worker = str(script_worker)

    with open('mysql_mng_node.sh', 'r') as f :
        script_mng = f.read()
    ud_mng = str(script_mng)
    
    with open('standalone_server.sh', 'r') as f :
        script_std = f.read()
    ud_std = str(script_std)

    with open('proxy.sh', 'r') as f :
        script_pxy = f.read()
    ud_pxy = str(script_pxy)

    with open('gatekeeper.sh', 'r') as f :
        script_gk = f.read()
    ud_gk = str(script_gk)

    #--------------------------------------Create the design pattern instances ------------------------------------------------------------

    # Create 3 intances with t2.micro as workers:
    Availabilityzons_Cluster1=['us-east-1a','us-east-1b','us-east-1a','us-east-1b','us-east-1a']
    instance_type_1 = "t2.micro"
    instance_type_2 = "t2.large"

    print("\n Creating instances : the master node ")
    # Creation of the manager/master instance:
    mng.t2 = create_instance_ec2(1,ami_id, instance_type_1,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons_Cluster1,"manager_node",ud_mng)
    # Waiting time for the setup of manager:
    time.sleep(300)

    print("\n Creating instances : the workers ")
    # Creation of the 3 workers:
    workers_t2= create_instance_ec2(3,ami_id, instance_type_1,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons_Cluster1,"worker",ud_worker)
    # Waiting time for the creation of the workers
    time.sleep(330)
    
    print("\n Creating instances : standalone_server ")
    # Creation of the standlone_server:
    std_alone.t2 = create_instance_ec2(1,ami_id, instance_type_1,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons_Cluster1,"standlone",ud_std)

    print("\n Creating instances : proxy ")
    # Creation of the proxy:
    proxy.t2 = create_instance_ec2(1,ami_id, instance_type_2,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons_Cluster1,"proxy",ud_pxy)

    print("\n Creating instances : gatekeeper ")
    # Creation of the gatekeeper:
    gk.t2 = create_instance_ec2(1,ami_id, instance_type_2,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons_Cluster1,"standlone",ud_gk)

    print("\n all instances created successfully")
    
    print('\n\n============================>SETUP ends<=====================================')

