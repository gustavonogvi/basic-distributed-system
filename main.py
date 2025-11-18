import multiprocessing
import time
import os
import numpy as np

from server_instance import run_server
from client_auto import run_client

N_SERVERS = 6

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def serial_test():
    rowsA, colsA, colsB = 6, 4, 5

    A = np.random.randint(0,10,(rowsA,colsA))
    B = np.random.randint(0,10,(colsA,colsB))

    np.save("A.npy", A)
    np.save("B.npy", B)

    C = A @ B

    with open("serial_result.txt", "w") as f:
        f.write(str(C))

    return A, B, C

def main():
    queue = multiprocessing.Queue()
    processes = []

    clear()
    print("[MAIN] Executando teste serial...\n")

    A, B, C = serial_test()
    print(f"[SERIAL] Matriz A: {A.shape}")
    print(f"[SERIAL] Matriz B: {B.shape}")
    print("[SERIAL] Resultado salvo em serial_result.txt\n")

    time.sleep(1)

    print("[MAIN] Iniciando servidores distribuídos...\n")

    for i in range(N_SERVERS):
        p = multiprocessing.Process(target=run_server, args=(i+1, queue), daemon=True)
        p.start()
        processes.append(p)
        time.sleep(0.1)

    server_ports = []
    while len(server_ports) < N_SERVERS:
        if not queue.empty():
            src, msg = queue.get()
            print(f"[{src}] {msg}")

            if "Iniciado na porta" in msg:
                port = int(msg.split("porta")[1].strip())
                server_ports.append(port)

    print(f"\n[MAIN] Servidores prontos: {server_ports}\n")

    # Rodar cliente
    print("[MAIN] Executando cliente distribuído...\n")
    run_client(server_ports, queue)

    print("\n[MAIN] Exibindo timeline completa:\n")
    time.sleep(0.5)

    while not queue.empty():
        src, msg = queue.get()
        if src == "RESULT":
            print("\n[MATRIZ FINAL]:\n")
            print(msg)
        else:
            print(f"[{src}] {msg}")

    print("\n[MAIN] Execução concluída.\n")


if __name__ == "__main__":
    main()
