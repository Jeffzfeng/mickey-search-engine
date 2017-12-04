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
while new_reservation == None:
        try:
                new_reservation = new_conn.run_instances(config_image, key_name=new_key.name, instance_type=config_instance_type, security_groups=[new_group.name])
        except:
                print "reservation not properly created.. trying again"

new_instance = new_reservation.instances[0]

#instance completed
while new_instance.state == 'pending':
        current_state = new_instance.state
        new_instance.update()
        print "state of instance is currently %s, should not take more than a minute to start running..." % (current_state)
        time.sleep(2)


print "instance is now running! ip address is at %s!" % (new_instance.ip_address)

key = paramiko.RSAKey.from_private_key_file(config_key_name+".pem") 
con = paramiko.SSHClient()
con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
connected = False

while not connected:
        try:
                con.connect(hostname = new_instance.ip_address.encode('utf-8'), username = "ec2-user", pkey = key)
                print "connected and ready to executed!"
                connected = True
        except:
                print "connection not yet ready - please wait a moment"
                time.sleep(2)

commands = ["cd lab4_group_9", "sudo yum install -y numpy", "sudo pip install bottle", "sudo pip install redis", "sudo yum install -y python-enchant", "sudo pip install pyenchant", "sudo yum install -y aspell-en enchant-aspell", "sudo pip install ConfigParser", "sudo easy_install -U boto"]

for command in commands:
    try:        
        print "Executing {}".format(command)
        stdin , stdout, stderr = con.exec_command(command) # this command is executed on the *remote* server
        #> /dev/null 2>&1 &
        print stdout.read()
        
    except:
        print( "Errors")
        print stderr.read()
        
os.system("scp -oStrictHostKeyChecking=no -i %s.pem -r %s ec2-user@%s:~/" % (config_key_name, config_directory, new_instance.ip_address.encode('utf-8')))
os.system("scp -oStrictHostKeyChecking=no -i %s.pem -r %s ec2-user@%s:~/lab4_group_9/." % (config_key_name, 'deployment.cfg', new_instance.ip_address.encode('utf-8')))
os.system("scp -oStrictHostKeyChecking=no -i %s.pem -r %s ec2-user@%s:~/lab4_group_9/." % (config_key_name, 'search_database.pickle', new_instance.ip_address.encode('utf-8')))
print "IP address available at %s, have fun!" % new_instance.ip_address.encode('utf-8')
os.system("ssh -o StrictHostKeyChecking=no -i %s.pem ec2-user@%s nohup sudo python lab4_group_9/lab4frontend.py" % (config_key_name, new_instance.ip_address.encode('utf-8')))
con.close()
