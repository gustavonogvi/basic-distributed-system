import multiprocessing
import os
import time

PORTS = [8001, 8002, 8003, 8004, 8005, 8006]
REFRESH_RATE = 1.0

# Usamos a Queue global gerada pelo multiprocessing
# O manager principal cria a queue, os servidores escrevem nela
# E esta UI captura o conteúdo via pipe

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def main():
    # Conectar à Queue existente
    # Ela é passada pelo multiprocessing internamente
    try:
        log_queue = multiprocessing.Queue._after_fork()  # for windows behavior
    except:
        log_queue = multiprocessing.Queue()

    status = {p: "Iniciando..." for p in PORTS}
    logs = {p: [] for p in PORTS}

    while True:
        while not log_queue.empty():
            port, message = log_queue.get()
            status[port] = message
            logs[port].append(message)

            if len(logs[port]) > 5:
                logs[port] = logs[port][-5:]

        clear_screen()

        print("--------------------------------------------------")
        print(" Painel de Servidores Distribuídos")
        print("--------------------------------------------------\n")

        for port in PORTS:
            print(f"Servidor {port}: {status[port]}")

        print("\n--------------------------------------------------")
        print(" Logs recentes por servidor")
        print("--------------------------------------------------\n")

        for port in PORTS:
            print(f"[{port}]")
            for line in logs[port]:
                print(f"  {line}")
            print()

        time.sleep(REFRESH_RATE)

if __name__ == "__main__":
    main()
