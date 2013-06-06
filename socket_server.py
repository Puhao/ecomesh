import socket
from struct import *

print "Creating Socket...."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 51234
host = ''
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))
print "Waiting for connections.."
s.listen(5)
while True:
	clientsock, clientaddr = s.accept()
	print "Got connections from", clientsock.getpeername()
	print "Client socket addr is", clientaddr
	while True:
		message = clientsock.recv(1024)
		if not message:
			break
		print "I receive:"+message
		for i in message:
			print "%x "	%(ord(i),),
		print "Received"
#	clientsock.close()