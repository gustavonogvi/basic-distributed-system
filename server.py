
import socket
import pickle
import numpy as np
from multiprocessing import Pool, cpu_count
import sys

class MatrixServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        
    def multiply_row(self, args):
        """
        Multiplica uma linha da submatriz A pela matriz B.
        Utilizado para paralelização com multiprocessing.
        """
        row, matrix_b = args
        return np.dot(row, matrix_b)
    
    def parallel_multiplication(self, submatrix_a, matrix_b):
        """
        Realiza multiplicação paralela usando multiprocessing.
        Cada linha da submatriz A é processada em paralelo.
        """
        num_processes = min(cpu_count(), len(submatrix_a))
        
        # Prepara argumentos para cada processo
        args = [(row, matrix_b) for row in submatrix_a]
        
        # Cria pool de processos e executa multiplicação
        with Pool(processes=num_processes) as pool:
            result = pool.map(self.multiply_row, args)
        
        return np.array(result)
    
    def start(self):
        """Inicia o servidor e aguarda conexões"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            print(f"[SERVIDOR] Aguardando conexão em {self.host}:{self.port}")
            
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"[SERVIDOR] Conexão estabelecida com {address}")
                
                # Aumenta buffer para transferências grandes
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
                
                try:
                    # Recebe tamanho dos dados
                    size_bytes = client_socket.recv(8)
                    data_size = int.from_bytes(size_bytes, byteorder='big')
                    
                    # Recebe dados em chunks
                    data = b''
                    remaining = data_size
                    while remaining > 0:
                        chunk = client_socket.recv(min(65536, remaining))
                        if not chunk:
                            break
                        data += chunk
                        remaining -= len(chunk)
                    
                    # Desserializa os dados
                    submatrix_a, matrix_b = pickle.loads(data)
                    print(f"[SERVIDOR] Recebido: submatriz A {submatrix_a.shape}, matriz B {matrix_b.shape}")
                    
                    # Realiza multiplicação paralela
                    result = self.parallel_multiplication(submatrix_a, matrix_b)
                    print(f"[SERVIDOR] Multiplicação concluída. Resultado: {result.shape}")
                    
                    # Serializa resultado
                    result_data = pickle.dumps(result, protocol=pickle.HIGHEST_PROTOCOL)
                    result_size = len(result_data)
                    
                    # Envia tamanho do resultado
                    client_socket.sendall(result_size.to_bytes(8, byteorder='big'))
                    
                    # Envia resultado em chunks
                    chunk_size = 65536
                    for i in range(0, result_size, chunk_size):
                        client_socket.sendall(result_data[i:i+chunk_size])
                    
                    print("[SERVIDOR] Resultado enviado ao cliente")
                    
                except Exception as e:
                    print(f"[SERVIDOR] Erro ao processar dados: {e}")
                finally:
                    client_socket.close()
                    
        except KeyboardInterrupt:
            print("\n[SERVIDOR] Encerrando servidor...")
        except Exception as e:
            print(f"[SERVIDOR] Erro: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

def main():
    """Função principal para iniciar o servidor"""
    # Configuração da porta (pode ser passada como argumento)
    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    server = MatrixServer(port=port)
    server.start()

if __name__ == "__main__":
    main()