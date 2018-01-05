import socket
import sys

try:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error as msg:
	print('Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1])
	sys.exit()
print('Socket Created')

host = 'kas-control'
#remote_ip = '217.123.221.17'
port = 7500

#try:
#    remote_ip = socket.gethostbyname(host)
#except socket.gaierror:
#    #could not resolve
#    print('Hostname could not be resolved. Exiting')
#    sys.exit()

remote_ip = "192.168.1.157"
try:
	s.connect((remote_ip , port))
	#break
except:
	a = input('Login failed, try again?: ')
	if (a == 'n'):
		s.close()
		sys.exit()
print(s.recv(4096).decode())

while(True):
	try:
		reply = input('Relpy: ')
		rep = reply.split()
		if (len(rep) >= 1):
			s.sendall(bytes(reply, 'utf-8'))
			if (rep[0] == 'exit'):
				break
		else:
			print('No statement made.')
	except socket.error:
		#Send failed
		print('Send failed')
		sys.exit()
	if (len(rep) >= 1):
		print('Message sent successfully')
		print(s.recv(16384).decode())
#print('Socket Connected to ' + host + ' on ip ' + remote_ip)
#print(s.recv(4096).decode())

#while(True):
	

s.close()
