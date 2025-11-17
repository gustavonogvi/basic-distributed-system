import socket
import pickle
import numpy as np


NUM_SERVERS = 3
SERVER_ADDRESSES = [
    ("localhost", 8001),
    ("localhost", 8002),
    ("localhost", 8003)
]


def generate_matrizes():
    rows_A = int(input("Número de linhas da matriz A: "))
    cols_A = int(input("Número de colunas da matriz A: "))
    
    cols_B = int(input("Número de colunas da matriz B: "))
    print()

    A = np.random.randint(0, 10, (rows_A, cols_A))
    B = np.random.randint(0, 10, (cols_A, cols_B))

    return A, B


def split_matriz(A, num_parts):
    return np.array_split(A, num_parts)


def send_to_server(server_address, subA, B):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(server_address)
            data = {"A_sub": subA, "B": B}
            serialized_data = pickle.dumps(data)

            # Envia os dados
            s.sendall(serialized_data)

            # Recebe resultado parcial
            result_data = s.recv(100000)
            C_sub = pickle.loads(result_data)

            print(f"Resultado parcial recebido de {server_address}: shape {C_sub.shape}")
            return C_sub

    except ConnectionRefusedError:
        print(f"Servidor {server_address} não está disponível!")
        return None


def main():
    print("=== CLIENTE DE MULTIPLICAÇÃO DISTRIBUÍDA ===\n")

    A, B = generate_matrizes()
    print("Matriz A:\n", A, "\n")
    print("Matriz B:\n", B, "\n")

    submatrices = split_matriz(A, NUM_SERVERS)
    print(f"\nMatriz A dividida em {NUM_SERVERS} partes.\n")

    partial_results = []

    for i, server in enumerate(SERVER_ADDRESSES):
        print(f"Enviando submatriz {i+1}/{NUM_SERVERS}...")
        C_sub = send_to_server(server, submatrices[i], B)

        if C_sub is not None:
            partial_results.append(C_sub)

    # Junta os resultados parciais
    C = np.vstack(partial_results)

    print("\n====== MATRIZ RESULTANTE C ======")
    print(C)


if __name__ == "__main__":
    main()
