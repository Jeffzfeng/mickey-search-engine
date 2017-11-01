#!/usr/bin/python
import boto.ec2 

#connects to a us-east-1 server using my key (a user of my AWS) 
#the conn object will now contain the connection and be used for the rest of the instantiation 
conn = boto.ec2.connect_to_region("us-east-2",
        aws_access_key_id='AKIAIJMHGFVAISZI7FHA',
        aws_secret_access_key='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')

#print when successful
print "connected to" + str(conn)

#create a keypair, and save pem file to access later
new_key = conn.create_key_pair('new_key_name')
new_key.save('.')

#create a basic security group
new_group = conn.create_security_group('csc326-group9', 'Girija-stud num: 999856534 and Jeff stud num: 1000820766 group')

#this security group will have access to the following ports
# allows HTTP to AWS server
new_group.authorize('tcp', 80, 80, '0.0.0.0/0')
# allows SSH to AWS server 
new_group.authorize('tcp', 22, 22, '0.0.0.0/0')
# for ICMP
new_group.authorize('icmp', -1, -1, '0.0.0.0/0')

#kick off instance into reservation queue
reservation = conn.run_instances('ami-c5062ba0', key_name='new_key_redis', instance_type='t1.micro', security_groups=['csc326-group9'])

#take first instance (the newly created one)
instances = reservation[0].instances

inst_object = instances[0]
    
#instance completed
print str(inst_object.state) + "now running" 
print "at ip address" + str(inst_object.ip_address)

