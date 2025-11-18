import socket
import pickle
import numpy as np
import sys
import time

def send_with_size(conn, data_bytes):
    size = len(data_bytes)
    conn.sendall(size.to_bytes(8, "big"))
    conn.sendall(data_bytes)

def recv_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise EOFError("Conexão fechada ao ler dados")
        buf += chunk
    return buf

def recv_with_size(conn):
    header = recv_exact(conn, 8)
    size = int.from_bytes(header, "big")
    payload = recv_exact(conn, size)
    return payload

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
            with conn:
                try:
                    payload = recv_with_size(conn)
                except Exception:
                    # fallback: ler tudo
                    data = b""
                    while True:
                        part = conn.recv(4096)
                        if not part:
                            break
                        data += part
                    payload = data

                data_obj = pickle.loads(payload)
                A_sub = data_obj["A_sub"]
                B = data_obj["B"]
                C = A_sub @ B

                out_bytes = pickle.dumps(C, protocol=pickle.HIGHEST_PROTOCOL)
                send_with_size(conn, out_bytes)

                log(f"Submatriz processada. Resultado: {C.shape}")

        except Exception as e:
            log(f"Erro: {e}")
            time.sleep(0.1)
