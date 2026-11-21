import time
from modules.router_interface import NetworkInterface

net_if = NetworkInterface(1) #Give an unique id
config_file = "config1.ini"
net_if.new_interface(2, 4, config_file, True) #interface_type, ip_version, config_file
#net_if._interface_up()

#Option 1: For testing that Hello messaging loops for 1 minute:
#time.sleep(60)

#Option 2: test looping until keyboard interrupt:
#try:
#    while True:
#        pass
#except KeyboardInterrupt:
#    net_if._hello_timer.stop()

#Test that interface is up and has values:
#net_if.sayhello()
#print(net_if)
