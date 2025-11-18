import socket
import pickle
import numpy as np
import time

"""
Servidor que usa bind(0) (porta alocada pelo SO). Comunicação:
- Recebe pickle do cliente (sem prefixo de tamanho).
- Processa: C_sub = A_sub @ B
- Envia o pickle de C_sub com prefixo de 8 bytes (tamanho em big-endian).
"""

def send_with_size(conn, data_bytes):
    size = len(data_bytes)
    conn.sendall(size.to_bytes(8, "big"))
    conn.sendall(data_bytes)

def recv_exact(conn, n):
    """Recebe exatamente n bytes (ou lança EOFError)."""
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise EOFError("Conexão fechada ao ler dados")
        buf += chunk
    return buf

def recv_with_size(conn):
    """Lê um prefixo de 8 bytes com o tamanho, depois lê o payload completo."""
    header = recv_exact(conn, 8)
    size = int.from_bytes(header, "big")
    payload = recv_exact(conn, size)
    return payload

def run_server(id, queue):
    HOST = "127.0.0.1"

    def log(msg):
        queue.put((f"SERVER {id}", msg))

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, 0))  # porta automática
        port = s.getsockname()[1]

        log(f"Iniciado na porta {port}")
        s.listen()
    except Exception as e:
        log(f"Erro ao iniciar servidor: {e}")
        return

    while True:
        try:
            conn, addr = s.accept()
            log(f"Conexão recebida de {addr}")
            with conn:
                # Recebe payload: assumimos que cliente enviou sem prefixo (compatível com cliente alterado)
                # Para consistência, aqui vamos aceitar dois formatos:
                # 1) cliente envia tamanho + payload
                # 2) cliente envia apenas payload (pickle direto) -> tentamos ler até EOF
                try:
                    # tentar ler header (8 bytes). Se falhar por timeout/EOF, tentar recv-all
                    conn.settimeout(1.0)
                    header = conn.recv(8, socket.MSG_PEEK)
                    if len(header) >= 8:
                        # tem header: usar protocolo com tamanho
                        payload = recv_with_size(conn)
                    else:
                        # sem header: ler tudo até EOF
                        conn.settimeout(2.0)
                        data = b""
                        while True:
                            part = conn.recv(4096)
                            if not part:
                                break
                            data += part
                        payload = data
                except Exception:
                    # fallback: ler até EOF
                    conn.settimeout(2.0)
                    data = b""
                    while True:
                        part = conn.recv(4096)
                        if not part:
                            break
                        data += part
                    payload = data

                payload_obj = pickle.loads(payload)

                A_sub = payload_obj["A_sub"]
                B = payload_obj["B"]

                log(f"Processando submatriz: {A_sub.shape}")
                C = A_sub @ B
                out_bytes = pickle.dumps(C, protocol=pickle.HIGHEST_PROTOCOL)

                # enviar com prefixo de tamanho (profissional)
                send_with_size(conn, out_bytes)
                log(f"Resultado enviado: {C.shape}")

        except Exception as e:
            log(f"Erro no loop do servidor: {e}")
            time.sleep(0.1)
