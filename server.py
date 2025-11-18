import socket
import pickle
import numpy as np
import sys
import time

def run_server(port, log_queue):
    HOST = "127.0.0.1"

    def log(msg):
        log_queue.put((port, msg))

    log(f"Servidor iniciado na porta {port}")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port))
        s.listen()
        log(f"Aguardando conexões...")
    except Exception as e:
        log(f"Erro ao iniciar servidor: {e}")
        return

    while True:
        try:
            conn, addr = s.accept()
            log(f"Conexão recebida de {addr}")

            data = conn.recv(500000)
            data = pickle.loads(data)

            A_sub = data["A_sub"]
            B = data["B"]

            C = A_sub @ B
            conn.sendall(pickle.dumps(C))

            log(f"Submatriz processada. Resultado: {C.shape}")

        except Exception as e:
            log(f"Erro: {e}")
            time.sleep(0.1)
