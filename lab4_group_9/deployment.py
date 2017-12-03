#!/usr/bin/python
import boto.ec2
import ConfigParser
import time
import os
import paramiko
import ConfigParser

configs = ConfigParser.ConfigParser()
configs.read('deployment.cfg')
# config for creating getting the connection 
config_region = configs.get('Connection','config_region')
config_aws_key_id = configs.get('Connection','config_aws_key_id')
config_aws_key_secret = configs.get('Connection','config_aws_key_secret')

# config for creating key for later use
config_key_name = configs.get('Key', 'config_key_name')

# config for creation of a security group, as well as allowed ports for that security group
config_security_group_name = configs.get('Security Group', 'config_security_group_name')
config_security_group_desc = configs.get('Security Group', 'config_security_group_desc')
config_HTTP = configs.getboolean('Security Group', 'config_HTTP')
config_SSH = configs.getboolean('Security Group', 'config_SSH')
config_ICMP = configs.getboolean('Security Group', 'config_ICMP')

# config for creation of a new instance on the current connection
config_image = configs.get('AMI options', 'config_image')
config_instance_type = configs.get('AMI options', 'config_instance_type')

# config for front end directory to copy into instance
config_directory = configs.get('Frontend Directory', 'config_directory')

#connects to a us-east-1 server using my key (a user of my AWS) 
#the new_conn object will now contain the connection and be used for the rest of the instantiation 
print "connecting to region %s" % (config_region) 
new_conn = boto.ec2.connect_to_region(config_region, 
        aws_access_key_id=config_aws_key_id,
        aws_secret_access_key=config_aws_key_secret) 
        
print "connected at" + str(new_conn)
time.sleep(1)

#create a keypair, and save pem file to access later
new_key = new_conn.create_key_pair(config_key_name)
new_key.save('.')
print "key created wth name %s" % (config_key_name)
time.sleep(1)

#create a basic security group
new_group = new_conn.create_security_group(config_security_group_name, config_security_group_desc)
print "new security group created %s" % (config_security_group_name)
time.sleep(1)

if config_HTTP:
        # allows HTTP to AWS server
        new_group.authorize('tcp', 80, 80, '0.0.0.0/0') 
        print "HTTP connections allowed on port 80"

if config_SSH:
        # allows SSH to AWS server 
        new_group.authorize('tcp', 22, 22, '0.0.0.0/0')
        print "SSH connections allowed on port 22"

if config_ICMP:
        # for ICMP
        new_group.authorize('icmp', -1, -1, '0.0.0.0/0')
        print "ICMP connections allowed on port -1"
time.sleep(1)

#kick off instance into reservation queue
new_reservation = new_conn.run_instances(config_image, key_name=new_key.name, instance_type=config_instance_type, security_groups=[new_group.name])
new_instance = new_reservation.instances[0]
#instance completed
while new_instance.state == 'pending':
        current_state = new_instance.state
        new_instance.update()
        print "state of instance is currently %s, should not take more than a minute to start running..." % (current_state)
        time.sleep(2)


print "instance is now running! ip address is at %s!" % (new_instance.ip_address)
copied = os.system("scp -i %s.pem -r %s ec2-user@%s:/" % (new_key.name.encode('utf-8'), config_directory, new_instance.ip_address.encode('utf-8')))
if copied:
        print "directory has been copied over to your new instance"
else:
   print "copy was not successful, please make sure the Frontend Directory exists"


time.sleep(1)

import paramiko
# paramiko setup 
key = paramiko.RSAKey.from_private_key_file(config_key_name+".pem") 
con = paramiko.SSHClient()
con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
connected = False

while not connected:
        try:
                con.connect(hostname = new_instance.ip_address.encode('utf-8'), username = "ec2-user", pkey = key)
                connected = True
        except:
                print "connection not yet ready - please wait a moment"
                time.sleep(2)
                
commands = [""]
for command in commands:
    print "Executing {}".format(command)
    stdin , stdout, stderr = con.exec_command(command) # this command is executed on the *remote* server
    print stdout.read()
    print( "Errors")
    print stderr.read()

con.close()
#new_conn.terminate_instances(instance_ids=[reservations[0].instances[0].id])