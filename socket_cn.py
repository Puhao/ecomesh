import socket

print "Creating Socket...."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 51423
host = "10.12.48.129"
print "Conneting to ----"+host
print "!"
s.connect((host, port))
print "Done"
print "Conneting from", s.getsockname()
print "Connecting to", s.getpeername()