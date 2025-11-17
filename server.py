import socket
import pickle
import numpy as np


def multiplicar_submatrix(data):
    A_sub = data["A_sub"]
    B = data["B"]
    C_sub = A_sub@B
    return C_sub


def start_server(port):
    HOST = "localhost"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, port))
        s.listen()
        print(f"Servidor ativo em {HOST}:{port} aguardando conexões...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Conexão recebida de {addr}")

                # Receber dados
                data = conn.recv(100000)
                data = pickle.loads(data)

                # Multiplicar
                result = multiplicar_submatrix(data)

                # Enviar resultado de volta
                serialized = pickle.dumps(result)
                conn.sendall(serialized)

                print(f"Resultado parcial enviado para o cliente. Shape: {result.shape}")


if __name__ == "__main__":
    port = int(input("Informe a porta deste servidor (8001, 8002 ou 8003): "))
    start_server(port)
