import socket
import pickle
import numpy as np
from concurrent.futures import ThreadPoolExecutor

PORTS = [8001, 8002, 8003, 8004, 8005, 8006]

def is_server_alive(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

def send_submatrix(port, A_sub, B):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", port))

        payload = pickle.dumps({"A_sub": A_sub, "B": B})
        s.sendall(payload)

        result = pickle.loads(s.recv(500000))
        s.close()

        print(f"Resposta recebida do servidor {port}")
        return result

    except:
        print(f"Falha no servidor {port}")
        return None

def main():
    print("Detectando servidores ativos...")
    active = [p for p in PORTS if is_server_alive(p)]
    print("Servidores encontrados:", active)

    rows = int(input("Linhas de A: "))
    cols = int(input("Colunas de A: "))
    colsB = int(input("Colunas de B: "))

    A = np.random.randint(0, 10, (rows, cols))
    B = np.random.randint(0, 10, (cols, colsB))

    submatrices = np.array_split(A, len(active))

    with ThreadPoolExecutor(max_workers=len(active)) as ex:
        futures = [ex.submit(send_submatrix, port, submatrices[i], B) 
                   for i, port in enumerate(active)]

    results = [f.result() for f in futures if f.result() is not None]
    C = np.vstack(results)

    print("\nMatriz resultante C:")
    print(C)


if __name__ == "__main__":
    main()
