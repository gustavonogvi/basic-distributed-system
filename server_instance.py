import socket
import pickle
import numpy as np
import time

def run_server(id, queue):
    HOST = "127.0.0.1"

    def log(msg):
        queue.put((f"SERVER {id}", msg))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, 0))  
    port = s.getsockname()[1]

    log(f"Iniciado na porta {port}")

    s.listen()

    while True:
        try:
            conn, addr = s.accept()
            log(f"Conexão recebida de {addr}")

            data = conn.recv(500000)
            payload = pickle.loads(data)

            A_sub = payload["A_sub"]
            B = payload["B"]

            log(f"Processando submatriz: {A_sub.shape}")
            C = A_sub @ B
            conn.sendall(pickle.dumps(C))

            log(f"Resultado enviado: {C.shape}")

        except Exception as e:
            log(f"Erro: {e}")
            time.sleep(0.1)
