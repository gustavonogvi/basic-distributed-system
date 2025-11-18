import socket
import pickle
import numpy as np
from concurrent.futures import ThreadPoolExecutor


def run_client(server_ports, queue):

    def log(msg):
        queue.put(("CLIENT", msg))

    def send(port, A_sub, B):
        log(f"Enviando submatriz para {port}: {A_sub.shape}")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(("127.0.0.1", port))

            s.sendall(pickle.dumps({"A_sub": A_sub, "B": B}))

            result = pickle.loads(s.recv(500000))
            log(f"Resposta recebida de {port}: {result.shape}")
            return result

        except:
            log(f"Falha ao comunicar com {port}")
            return None

    rowsA, colsA, colsB = 6, 4, 5
    A = np.load("A.npy")
    B = np.load("B.npy")

    log(f"Matriz A carregada: {A.shape}")
    log(f"Matriz B carregada: {B.shape}")

    subs = np.array_split(A, len(server_ports))
    log("Submatrizes preparadas")

    with ThreadPoolExecutor(max_workers=len(server_ports)) as ex:
        futures = [
            ex.submit(send, port, subs[i], B) 
            for i, port in enumerate(server_ports)
        ]

    results = [f.result() for f in futures if f.result() is not None]

    if results:
        C = np.vstack(results)
        queue.put(("RESULT", C))
        log(f"Matriz final construída: {C.shape}")
    else:
        log("Nenhum resultado recebido")
