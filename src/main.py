from modules.router_interface import NetworkInterface

net_if = NetworkInterface(1) #Give an unique id
config_file = "config1.ini"
net_if.new_interface(2, 4, config_file) #interface_type, ip_version, config_file
print(f"It works: {net_if.sayhello()}")
#print(net_if)
