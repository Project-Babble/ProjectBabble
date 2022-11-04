import socket
import pickle
import struct
import random

def send_data(conn, data):
    serialized_data = pickle.dumps(data)
    conn.sendall(struct.pack('>I', len(serialized_data)))
    conn.sendall(serialized_data)


def receive_data(conn):
    data_size = struct.unpack('>I', conn.recv(4))[0]
    received_payload = b""
    reamining_payload_size = data_size
    while reamining_payload_size != 0:
        received_payload += conn.recv(reamining_payload_size)
        reamining_payload_size = data_size - len(received_payload)
    data = pickle.loads(received_payload)

    return data

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 50000))
predictions = []
for i in range(200):
    prediction = []
    for j in range(83):
        blendshape = round(random.uniform(0, 1), 3)
        prediction.append(blendshape)
    prediction.append(f'{i}.png')
    predictions.append(prediction)
print('generated blendshapes')
data = pickle.dumps(predictions)

send_data(s, data)
