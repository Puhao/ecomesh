import socket

print "Creating Socket...."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 51423
host = "10.12.48.129"
print "Conneting to ----"+host
print "!"
try:
	print "Cont!"
	s.connect((host, port))
except socket.error, e:
	print "Error happen, %s" %(e,)

print "Done"
print "Conneting from", s.getsockname()
print "Connecting to", s.getpeername()