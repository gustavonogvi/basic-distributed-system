import multiprocessing
import time
import numpy as np
import os
import socket
import pickle
import json
import csv
from datetime import datetime

from server_instance import run_server


# ===============================================================
# Comunicacao com envio de tamanho
# ===============================================================

def send_with_size(sock, data_bytes):
    sock.sendall(len(data_bytes).to_bytes(8, "big"))
    sock.sendall(data_bytes)

def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("Conexao fechada ao ler dados")
        buf += chunk
    return buf

def recv_with_size(sock):
    header = recv_exact(sock, 8)
    size = int.from_bytes(header, "big")
    payload = recv_exact(sock, size)
    return payload


# ===============================================================
# Multiplicacao distribuida
# ===============================================================

def distributed_multiply(A, B, ports):
    subs = np.array_split(A, len(ports))
    results = []

    for i, port in enumerate(ports):
        A_sub = subs[i]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(40)
            s.connect(("127.0.0.1", port))

            payload = pickle.dumps({"A_sub": A_sub, "B": B}, protocol=pickle.HIGHEST_PROTOCOL)
            send_with_size(s, payload)

            resp_bytes = recv_with_size(s)
            C_sub = pickle.loads(resp_bytes)
            results.append(C_sub)

    return np.vstack(results)


# ===============================================================
# Servidores
# ===============================================================

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
                port = int(msg.split("porta")[1].strip())
                ports.append(port)
        except:
            if time.time() - start_time > 20:
                raise RuntimeError("Falha ao iniciar servidores")

    return procs, ports

def stop_servers(procs):
    for p in procs:
        try:
            p.terminate()
        except:
            pass


# ===============================================================
# Registro e pastas
# ===============================================================

RESULTS_DIR = "test_results"

def prepare_results_folder():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

def ensure_test_folder(name):
    path = os.path.join(RESULTS_DIR, name.replace(" ", "_"))
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def save_matrix_txt(path, matrix, title):
    with open(path, "w") as f:
        f.write(f"{title}\n\n")
        for row in matrix:
            f.write(str(row.tolist()) + "\n")


def save_results_json(results):
    with open(os.path.join(RESULTS_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=4)

def save_results_csv(results):
    with open(os.path.join(RESULTS_DIR, "results.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "nome",
            "A_shape",
            "B_shape",
            "tempo_serial",
            "tempo_distribuido",
            "diferenca",
            "erro_max",
            "correto"
        ])
        for name, data in results.items():
            writer.writerow([
                name,
                data["A_shape"],
                data["B_shape"],
                data["tempo_serial"],
                data["tempo_distribuido"],
                data["diferenca"],
                data["erro_max"],
                data["correto"]
            ])

def save_results_txt(results):
    with open(os.path.join(RESULTS_DIR, "report.txt"), "w") as f:
        f.write("RELATORIO DE TESTES DISTRIBUIDOS\n")
        f.write(f"Data: {datetime.now()}\n")
        f.write("================================\n\n")

        for name, data in results.items():
            f.write(f"{name}\n")
            f.write(f"  A: {data['A_shape']}\n")
            f.write(f"  B: {data['B_shape']}\n")
            f.write(f"  Tempo serial:      {data['tempo_serial']:.6f} s\n")
            f.write(f"  Tempo distribuido: {data['tempo_distribuido']:.6f} s\n")
            f.write(f"  Diferenca:         {data['diferenca']:.6f} s\n")
            f.write(f"  Erro maximo:       {data['erro_max']:.6f}\n")
            f.write(f"  Correto:           {data['correto']}\n")
            f.write("--------------------------------\n")


# ===============================================================
# Benchmark (sem mostrar matrizes na tela)
# ===============================================================

def run_benchmark(test_name, A, B, ports, results_dict):
    print(f"\n===== {test_name} =====")
    print(f"A shape: {A.shape}")
    print(f"B shape: {B.shape}")

    folder = ensure_test_folder(test_name)

    # Serial
    t1 = time.perf_counter()
    C_serial = A @ B
    t2 = time.perf_counter()

    # Distribuido
    t3 = time.perf_counter()
    C_dist = distributed_multiply(A, B, ports)
    t4 = time.perf_counter()

    # Medidas
    tempo_serial = t2 - t1
    tempo_distrib = t4 - t3
    diferenca = tempo_distrib - tempo_serial
    erro_max = float(np.max(np.abs(C_serial - C_dist)))
    correto = np.allclose(C_serial, C_dist)

    # Mostra apenas informacoes importantes
    print("Correto:", correto)
    print("Erro maximo:", erro_max)
    print(f"Tempo serial:      {tempo_serial:.6f} s")
    print(f"Tempo distribuido: {tempo_distrib:.6f} s")
    print(f"Diferenca:         {diferenca:.6f} s")

    # Salvar matrizes em TXT
    save_matrix_txt(os.path.join(folder, "C_serial.txt"), C_serial, "Resultado Serial")
    save_matrix_txt(os.path.join(folder, "C_distrib.txt"), C_dist, "Resultado Distribuido")

    # Registrar sumario
    results_dict[test_name] = {
        "A_shape": list(A.shape),
        "B_shape": list(B.shape),
        "tempo_serial": tempo_serial,
        "tempo_distribuido": tempo_distrib,
        "diferenca": diferenca,
        "erro_max": erro_max,
        "correto": bool(correto)
    }


# ===============================================================
# Main
# ===============================================================

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("==== TESTE DE ARQUITETURA DISTRIBUIDA ====\n")

    prepare_results_folder()

    N_SERVERS = 6
    print(f"Iniciando {N_SERVERS} servidores...")
    procs, ports = start_servers(N_SERVERS)
    print("Servidores prontos:", ports)

    results = {}

    try:
        # Teste pequeno
        run_benchmark(
            "Teste Pequeno",
            np.random.randint(0, 10, (20, 30)),
            np.random.randint(0, 10, (30, 40)),
            ports, results
        )

        # Teste medio
        run_benchmark(
            "Teste Medio",
            np.random.randint(0, 10, (200, 300)),
            np.random.randint(0, 10, (300, 150)),
            ports, results
        )

        # ================================
        # TESTE GRANDE DE VERDADE
        # ================================
        print("\nPreparando matrizes muito grandes... isso pode levar alguns segundos...")

        A = np.random.randint(0, 10, (2000, 1000))
        B = np.random.randint(0, 10, (1000, 1500))

        run_benchmark(
            "Teste Grande",
            A, B,
            ports, results
        )

        # Salvando relatorios
        print("\nSalvando relatorios...")
        save_results_json(results)
        save_results_csv(results)
        save_results_txt(results)
        print("Relatorios salvos em test_results/")

    finally:
        stop_servers(procs)


if __name__ == "__main__":
    main()
