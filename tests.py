import multiprocessing
import time
import numpy as np
import os
import socket
import pickle
import sys

from server_instance import run_server

def send_with_size(sock, data_bytes):
    sock.sendall(len(data_bytes).to_bytes(8, "big"))
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

def distributed_multiply(A, B, ports):
    subs = np.array_split(A, len(ports))
    results = []

    for i, port in enumerate(ports):
        A_sub = subs[i]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(15)
                s.connect(("127.0.0.1", port))
                payload = pickle.dumps({"A_sub": A_sub, "B": B}, protocol=pickle.HIGHEST_PROTOCOL)
                send_with_size(s, payload)
                resp_bytes = recv_with_size(s)
                C_sub = pickle.loads(resp_bytes)
                results.append(C_sub)
        except Exception as e:
            print(f"Falha no servidor {port}: {e}")

    if not results:
        raise RuntimeError("Nenhum resultado foi obtido no modo distribuído.")

    return np.vstack(results)

def start_servers(n):
    queue = multiprocessing.Queue()
    procs = []
    ports = []

    for i in range(n):
        p = multiprocessing.Process(target=run_server, args=(i + 1, queue), daemon=True)
        p.start()
        procs.append(p)

    start_time = time.time()
    while len(ports) < n:
        try:
            src, msg = queue.get(timeout=5.0)
            if "porta" in msg:
                try:
                    port = int(msg.split("porta")[1].strip())
                    ports.append(port)
                except Exception:
                    pass
        except Exception:
            if time.time() - start_time > 20:
                raise RuntimeError("Tempo esgotado ao iniciar servidores.")
    return procs, ports

def stop_servers(procs):
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass

def run_benchmark(test_name, A, B, ports):
    print(f"\n===== {test_name} =====")
    print(f"Matriz A: {A.shape}")
    print(f"Matriz B: {B.shape}")

    t1 = time.perf_counter()
    C_serial = A @ B
    t2 = time.perf_counter()

    t3 = time.perf_counter()
    C_dist = distributed_multiply(A, B, ports)
    t4 = time.perf_counter()

    if np.allclose(C_serial, C_dist):
        print("Resultado CORRETO (serial == distribuído)")
    else:
        print("ERRO: Resultados diferentes entre serial e distribuído")
        raise AssertionError("Resultados não batem")

    print(f"Tempo serial:      {t2 - t1:.6f} s")
    print(f"Tempo distribuído: {t4 - t3:.6f} s")
    print("Diferença:", (t4 - t3) - (t2 - t1), "s")

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("==== TESTE DE ARQUITETURA DISTRIBUÍDA ====\n")

    N_SERVERS = 6
    print(f"Iniciando {N_SERVERS} servidores...")
    procs, ports = start_servers(N_SERVERS)
    print("Servidores prontos nas portas:", ports)

    try:
        # Teste Pequeno
        A = np.random.randint(0, 10, (20, 30))
        B = np.random.randint(0, 10, (30, 40))
        run_benchmark("Teste Pequeno", A, B, ports)

        # Teste Médio
        A = np.random.randint(0, 10, (200, 300))
        B = np.random.randint(0, 10, (300, 150))
        run_benchmark("Teste Médio", A, B, ports)

        A = np.random.randint(0, 10, (800, 600))
        B = np.random.randint(0, 10, (600, 400))
        run_benchmark("Teste Grande", A, B, ports)

        print("\nTodos os testes passaram ✔")

    finally:
        print("\nEncerrando servidores...")
        stop_servers(procs)

if __name__ == "__main__":
    main()
