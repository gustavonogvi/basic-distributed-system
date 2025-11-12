import socket
import pickle
import numpy as np


NUM_SERVERS = 5
SERVER_ADDRESSES = [
    ("localhost", 8001),
    ("localhost", 8002),
    ("localhost", 8003),
    ("localhost", 8004),
    ("localhost", 8005)
]


def generate_matrizes():
    rows_A = int(input("Número de linhas da matriz A: "))
    cols_A = int(input("Número de colunas da matriz A: "))
    print
    cols_B = int(input("Número de colunas da matriz B: "))
    print()

    # A tem (rows_A x cols_A)
    # B tem (cols_A x cols_B) para ser multiplicável
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
            s.sendall(serialized_data)
            print(f"Enviado para {server_address}: subA {subA.shape}, B {B.shape}")
    except ConnectionRefusedError:
        print(f"Servidor {server_address} não está disponível. Ignorando envio.")



def main():
    print("=== CLIENTE DE MULTIPLICAÇÃO DISTRIBUÍDA ===\n")

    # 1. Geração dinâmica das matrizes
    A, B = generate_matrizes()
    print("Matriz A:\n", A, "\n")
    print("Matriz B:\n", B, "\n")

    # 2. Divisão da matriz A entre os servidores
    submatrices = split_matriz(A, NUM_SERVERS)
    print(f"🔹 Matriz A foi dividida em {NUM_SERVERS} submatrizes.\n")

    # 3. Envio de cada submatriz para o respectivo servidor
    for i, server in enumerate(SERVER_ADDRESSES):
        print(f"Enviando submatriz {i+1}/{NUM_SERVERS}...")
        send_to_server(server, submatrices[i], B)

    print("\nTodas as submatrizes foram enviadas com sucesso!\n")


if __name__ == "__main__":
    main()
