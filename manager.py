import multiprocessing
import subprocess
import time
import sys
from server_instance import run_server

PORTS = [8001, 8002, 8003, 8004, 8005, 8006]

def start_servers(log_queue):
    processes = []

    for port in PORTS:
        p = multiprocessing.Process(
            target=run_server,
            args=(port, log_queue),
            daemon=True
        )
        p.start()
        processes.append(p)
        time.sleep(0.1)

    return processes

def main():
    log_queue = multiprocessing.Queue()

    print("Iniciando servidores em background...")
    procs = start_servers(log_queue)

    print("Abrindo painel em nova janela...")
    
    cmd = f'{sys.executable} manager_ui.py'
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

    print("Painel aberto em outra janela.")
    print("Use CTRL+C para encerrar este terminal (os servidores continuam).")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando servidores...")
        for p in procs:
            p.terminate()

if __name__ == "__main__":
    main()
