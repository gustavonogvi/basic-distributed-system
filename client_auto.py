import socket
import pickle
import numpy as np
from concurrent.futures import ThreadPoolExecutor

def log(queue, msg):
    queue.put(("CLIENT", msg))

def send_with_size(sock, data_bytes):
    size = len(data_bytes)
    sock.sendall(size.to_bytes(8, "big"))
    sock.sendall(data_bytes)

def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("Conexão fechada ao ler dados")
        buf += chunk
    return buf

def recv_with_size(sock):
    header = recv_exact(sock, 8)
    size = int.from_bytes(header, "big")
    payload = recv_exact(sock, size)
    return payload

def send(port, A_sub, B, queue):
    log(queue, f"Enviando submatriz para {port}: {A_sub.shape}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect(("127.0.0.1", port))

            payload = pickle.dumps({"A_sub": A_sub, "B": B}, protocol=pickle.HIGHEST_PROTOCOL)

            # enviar com prefixo de tamanho
            send_with_size(s, payload)

            # receber com prefixo de tamanho
            resp_bytes = recv_with_size(s)
            result = pickle.loads(resp_bytes)

            log(queue, f"Resposta recebida de {port}: {result.shape}")
            return result

    except Exception as e:
        log(queue, f"Falha ao comunicar com {port}: {e}")
        return None

def run_client(server_ports, queue):
    rowsA, colsA, colsB = 6, 4, 5
    A = np.load("A.npy")
    B = np.load("B.npy")

    log(queue, f"Matriz A carregada: {A.shape}")
    log(queue, f"Matriz B carregada: {B.shape}")

    subs = np.array_split(A, len(server_ports))
    log(queue, "Submatrizes preparadas")

    with ThreadPoolExecutor(max_workers=len(server_ports)) as ex:
        futures = [
            ex.submit(send, server_ports[i], subs[i], B, queue) 
            for i in range(len(server_ports))
        ]

    results = [f.result() for f in futures if f.result() is not None]

    if results:
        C = np.vstack(results)
        queue.put(("RESULT", C))
        log(queue, f"Matriz final construída: {C.shape}") 
    else:
        log(queue, "Nenhum resultado recebido")
