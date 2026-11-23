import socket
HOST = "10.0.0.210"  # The receiver's hostname or IP address
PORT =  65435  # The port used

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    result=s.recvfrom(20123)
    print("Received message:", result)