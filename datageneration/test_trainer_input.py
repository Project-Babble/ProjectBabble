import random
import socket
import pickle
import math
import struct



def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


    



                # Generates random values for blendshape predictions and file names.

predictions = []
for i in range(200):
    prediction = []
    for j in range(72):
        blendshape = round(random.uniform(0, 1), 3)
        prediction.append(blendshape)
    #prediction.append(f'{i}.png')
    predictions.append(prediction)
print('generated blendshapes')
                                
                                
                                # Establish a connection to the render server
HOST = 'localhost'
PORT = 50000
HEADERSIZE = 10
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))




                                    # Send predicted values
send_msg(s, pickle.dumps(predictions))


                                    # Confirmation from the server that blendshapes were recieved
ack = pickle.loads(recv_msg(s))
print(ack)

                        # Wait on finished renders

                                    # Render Server notifies that rendering has completed 
fin = pickle.loads(recv_msg(s))
print(fin)






