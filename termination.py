import boto.ec2
import ConfigParser
import time

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
new_conn = boto.ec2.connect_to_region(config_region, 
        aws_access_key_id=config_aws_key_id,
        aws_secret_access_key=config_aws_key_secret) 
        
reservations = new_conn.get_all_reservations()

for reservation in reservations:
    if reservation.instances[0].key_name == config_key_name:
        print "found instance -- terminating!"
        new_conn.terminate_instances(instance_ids=[reservation.instances[0].id])
        while reservation.instances[0].state != 'terminated':
            reservation.instances[0].update()
            print "please wait ... terminating (this may take around a minute)"
            time.sleep(2)
    
print "instance successfully terminated!"

all_keys = new_conn.get_all_key_pairs()

for key in all_keys:
    if(key.name.encode('utf-8')!='new_key_name'):
        try: 
            new_conn.delete_key_pair(key.name.encode('utf-8'))
            print "key succesfully deleted from connection!"
        except:
            print "could not delete key, might need to manually remove key %s from connection" % config_key_name

all_groups = new_conn.get_all_security_groups()

for group in all_groups:
    if(group.name.encode('utf-8')!='csc326-group9'):
        try:
            new_conn.delete_security_group(group.name.encode('utf-8')) 
            print "security group successfully deleted from connection!"
        except:
            print "could not delete security group, might need to manually remove private group %s from connection" % config_security_group_name