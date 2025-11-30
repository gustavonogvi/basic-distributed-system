import socket
import pickle
import numpy as np
import time
import matplotlib.pyplot as plt
import json
from datetime import datetime
import os

class MatrixClient:
    def __init__(self, servers):
        """
        Inicializa o cliente com lista de servidores.
        servers: lista de tuplas [(host, port), ...]
        """
        self.servers = servers
        self.num_servers = len(servers)
    
    def generate_matrices(self, rows_a, cols_a, cols_b):
        """Gera matrizes A e B aleatórias"""
        A = np.random.randint(-10, 10, size=(rows_a, cols_a))
        B = np.random.randint(-10, 10, size=(cols_a, cols_b))
        return A, B
    
    def split_matrix(self, matrix, num_parts):
        """
        Divide a matriz A em submatrizes para distribuição.
        Retorna lista de submatrizes.
        """
        rows = matrix.shape[0]
        rows_per_part = rows // num_parts
        submatrices = []
        
        for i in range(num_parts):
            start_row = i * rows_per_part
            if i == num_parts - 1:
                # Última parte pega todas as linhas restantes
                end_row = rows
            else:
                end_row = (i + 1) * rows_per_part
            
            submatrices.append(matrix[start_row:end_row])
        
        return submatrices
    
    def send_to_server(self, server_addr, submatrix_a, matrix_b):
        """
        Envia submatriz para um servidor e recebe resultado.
        Otimizado para grandes volumes de dados.
        """
        try:
            # Cria conexão com servidor
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(server_addr)
            
            # Aumenta buffer para transferências grandes
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            
            # Serializa com protocolo otimizado
            data = pickle.dumps((submatrix_a, matrix_b), protocol=pickle.HIGHEST_PROTOCOL)
            data_size = len(data)
            
            # Envia tamanho primeiro
            client_socket.sendall(data_size.to_bytes(8, byteorder='big'))
            
            # Envia dados em chunks maiores
            chunk_size = 65536  # 64KB chunks
            for i in range(0, data_size, chunk_size):
                client_socket.sendall(data[i:i+chunk_size])
            
            # Recebe tamanho do resultado
            result_size_bytes = client_socket.recv(8)
            result_size = int.from_bytes(result_size_bytes, byteorder='big')
            
            # Recebe resultado em chunks
            result_data = b''
            remaining = result_size
            while remaining > 0:
                chunk = client_socket.recv(min(65536, remaining))
                if not chunk:
                    break
                result_data += chunk
                remaining -= len(chunk)
            
            result = pickle.loads(result_data)
            client_socket.close()
            
            return result
            
        except Exception as e:
            print(f"[ERRO] Falha ao comunicar com servidor {server_addr}: {e}")
            return None
    
    def distribute_multiplication(self, A, B, show_details=True):
        """
        Distribui multiplicação de matrizes entre servidores.
        Retorna (resultado, tempo_execucao)
        """
        start_time = time.time()
        
        if show_details:
            print(f"\n{'='*60}")
            print(f"[CLIENTE] Iniciando multiplicação distribuída")
            print(f"[CLIENTE] Matriz A: {A.shape}, Matriz B: {B.shape}")
            print(f"[CLIENTE] Número de servidores: {self.num_servers}")
        
        # Divide matriz A em submatrizes
        submatrices = self.split_matrix(A, self.num_servers)
        
        if show_details:
            print(f"[CLIENTE] Matriz A dividida em {len(submatrices)} partes")
            for i, sub in enumerate(submatrices):
                print(f"  - Submatriz {i+1}: {sub.shape}")
        
        # Envia para servidores e coleta resultados
        results = []
        for i, (server_addr, submatrix) in enumerate(zip(self.servers, submatrices)):
            if show_details:
                print(f"\n[CLIENTE] Enviando para servidor {i+1} ({server_addr[0]}:{server_addr[1]})...")
            
            result = self.send_to_server(server_addr, submatrix, B)
            
            if result is not None:
                results.append(result)
                if show_details:
                    print(f"[CLIENTE] Resultado recebido do servidor {i+1}: {result.shape}")
            else:
                raise Exception(f"Falha ao receber resultado do servidor {i+1}")
        
        # Concatena resultados
        final_result = np.vstack(results)
        end_time = time.time()
        execution_time = end_time - start_time
        
        if show_details:
            print(f"\n[CLIENTE] Multiplicação concluída!")
            print(f"[CLIENTE] Matriz resultado C: {final_result.shape}")
            print(f"[CLIENTE] Tempo de execução: {execution_time:.4f} segundos")
            print(f"{'='*60}\n")
        
        return final_result, execution_time
    
    def verify_result(self, A, B, C_distributed):
        """Verifica se o resultado distribuído está correto"""
        C_numpy = np.dot(A, B)
        return np.allclose(C_distributed, C_numpy)


def modo_apresentacao():
    """Modo interativo para apresentação em sala"""
    print("\n" + "="*70)
    print("  MULTIPLICAÇÃO DISTRIBUÍDA DE MATRIZES")
    print("  Trabalho de Computação Paralela e Concorrente")
    print("="*70)
    
    # Configuração dos servidores
    print("\n[CONFIG] Configurando servidores...")
    num_servers = int(input("Quantos servidores deseja utilizar? (recomendado: 2-4): "))
    
    servers = []
    for i in range(num_servers):
        print(f"\nServidor {i+1}:")
        host = input(f"  Host (deixe vazio para 'localhost'): ").strip() or 'localhost'
        port = int(input(f"  Porta (ex: {5000+i}): "))
        servers.append((host, port))
    
    # Dimensões das matrizes
    print("\n[CONFIG] Dimensões das matrizes:")
    rows_a = int(input("Número de linhas da matriz A: "))
    cols_a = int(input("Número de colunas da matriz A (e linhas de B): "))
    cols_b = int(input("Número de colunas da matriz B: "))
    
    # Cria cliente e executa
    client = MatrixClient(servers)
    
    print("\n[CLIENTE] Gerando matrizes...")
    A, B = client.generate_matrices(rows_a, cols_a, cols_b)
    
    print("\n[CLIENTE] Matriz A:")
    print(A)
    print("\n[CLIENTE] Matriz B:")
    print(B)
    
    input("\nPressione ENTER para iniciar a multiplicação distribuída...")
    
    # Executa multiplicação SERIAL
    print("\n[TESTE 1] Executando multiplicação SERIAL (NumPy)...")
    C_serial, tempo_serial = multiplicacao_serial(A, B)
    print(f"[SERIAL] Tempo: {tempo_serial:.4f} segundos")
    
    input("\nPressione ENTER para executar a versão DISTRIBUÍDA...")
    
    # Executa multiplicação DISTRIBUÍDA
    print("\n[TESTE 2] Executando multiplicação DISTRIBUÍDA...")
    C, tempo_dist = client.distribute_multiplication(A, B, show_details=True)
    
    print("\n[CLIENTE] Matriz Resultado C:")
    print(C)
    
    # Verificação
    print("\n[VERIFICAÇÃO] Comparando com resultado do NumPy...")
    if client.verify_result(A, B, C):
        print("✓ Resultado CORRETO! A multiplicação distribuída funcionou perfeitamente.")
    else:
        print("✗ Resultado INCORRETO! Há um problema na implementação.")
    
    # Comparação de desempenho
    print("\n" + "="*70)
    print("  COMPARAÇÃO DE DESEMPENHO")
    print("="*70)
    print(f"\n{'Método':<20} {'Tempo':<15} {'Performance'}")
    print("-" * 70)
    print(f"{'Serial (NumPy)':<20} {tempo_serial:>10.4f}s")
    print(f"{'Distribuído':<20} {tempo_dist:>10.4f}s")
    print("-" * 70)
    
    if tempo_dist < tempo_serial:
        speedup = tempo_serial / tempo_dist
        print(f"\n✓ Distribuído foi {speedup:.2f}x MAIS RÁPIDO!")
        print(f"  Ganho de tempo: {(tempo_serial - tempo_dist):.4f}s")
    else:
        slowdown = tempo_dist / tempo_serial
        print(f"\n✗ Serial foi {slowdown:.2f}x mais rápido")
        print(f"  Overhead distribuído: {(tempo_dist - tempo_serial):.4f}s")
        print(f"\n  💡 Para matrizes pequenas, o overhead de comunicação")
        print(f"     pode ser maior que o ganho de paralelização.")
        print(f"     Teste com matrizes maiores (ex: 200×200 ou mais)!")
    
    print("\n" + "="*70)


def multiplicacao_serial(A, B):
    """Multiplicação serial usando NumPy para comparação"""
    start_time = time.time()
    C = np.dot(A, B)
    tempo = time.time() - start_time
    return C, tempo


def modo_benchmark():
    """Modo de testes em massa para geração de gráficos com comparação serial vs distribuído"""
    print("\n" + "="*70)
    print("  MODO BENCHMARK - COMPARAÇÃO SERIAL VS DISTRIBUÍDO")
    print("="*70)
    
    # Configuração
    num_servers = int(input("\nNúmero de servidores: "))
    servers = [('localhost', 5000 + i) for i in range(num_servers)]
    
    print("\nServidores configurados:")
    for i, srv in enumerate(servers):
        print(f"  {i+1}. {srv[0]}:{srv[1]}")
    
    # Parâmetros dos testes
    print("\n[CONFIG] Parâmetros dos testes:")
    tamanhos = input("Tamanhos das matrizes (ex: 10,50,100,200,400,800): ")
    tamanhos = [int(x.strip()) for x in tamanhos.split(',')]
    repeticoes = int(input("Repetições por tamanho (recomendado: 3-5): "))
    
    client = MatrixClient(servers)
    resultados = []
    
    print(f"\n[BENCHMARK] Iniciando {len(tamanhos)} testes com {repeticoes} repetições cada...")
    print("="*70)
    
    for tamanho in tamanhos:
        print(f"\n[TESTE] Matrizes {tamanho}x{tamanho}...")
        tempos_dist = []
        tempos_serial = []
        
        # Gera matrizes uma vez para ambos os testes
        A, B = client.generate_matrices(tamanho, tamanho, tamanho)
        
        for rep in range(repeticoes):
            print(f"  Repetição {rep+1}/{repeticoes}...")
            
            # Teste SERIAL
            print(f"    Serial...", end=' ')
            _, tempo_s = multiplicacao_serial(A, B)
            tempos_serial.append(tempo_s)
            print(f"{tempo_s:.4f}s")
            
            # Teste DISTRIBUÍDO
            print(f"    Distribuído...", end=' ')
            C_dist, tempo_d = client.distribute_multiplication(A, B, show_details=False)
            
            # Verifica correção
            if not client.verify_result(A, B, C_dist):
                print("ERRO!")
                continue
            
            tempos_dist.append(tempo_d)
            print(f"{tempo_d:.4f}s")
        
        tempo_medio_dist = np.mean(tempos_dist)
        tempo_std_dist = np.std(tempos_dist)
        tempo_medio_serial = np.mean(tempos_serial)
        tempo_std_serial = np.std(tempos_serial)
        
        speedup = tempo_medio_serial / tempo_medio_dist if tempo_medio_dist > 0 else 0
        
        resultados.append({
            'tamanho': tamanho,
            'tempo_medio_distribuido': tempo_medio_dist,
            'tempo_std_distribuido': tempo_std_dist,
            'tempo_medio_serial': tempo_medio_serial,
            'tempo_std_serial': tempo_std_serial,
            'speedup': speedup,
            'tempos_individuais_dist': tempos_dist,
            'tempos_individuais_serial': tempos_serial
        })
        
        print(f"  → Serial: {tempo_medio_serial:.4f}s (±{tempo_std_serial:.4f}s)")
        print(f"  → Distribuído: {tempo_medio_dist:.4f}s (±{tempo_std_dist:.4f}s)")
        print(f"  → Speedup: {speedup:.2f}x")
    
    # Salva resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            'num_servers': num_servers,
            'servers': servers,
            'resultados': resultados
        }, f, indent=2)
    
    print(f"\n[SALVO] Resultados salvos em: {filename}")
    
    # Gera gráficos
    gerar_graficos_comparacao(resultados, num_servers, timestamp)
    
    print("\n" + "="*70)


def gerar_graficos_comparacao(resultados, num_servers, timestamp):
    """Gera gráficos individuais comparando serial vs distribuído"""
    
    tamanhos = [r['tamanho'] for r in resultados]
    tempos_dist = [r['tempo_medio_distribuido'] for r in resultados]
    tempos_serial = [r['tempo_medio_serial'] for r in resultados]
    stds_dist = [r['tempo_std_distribuido'] for r in resultados]
    stds_serial = [r['tempo_std_serial'] for r in resultados]
    speedups = [r['speedup'] for r in resultados]
    
    # ========== GRÁFICO 1: Comparação Direta Serial vs Distribuído ==========
    plt.figure(figsize=(12, 8))
    
    x = np.arange(len(tamanhos))
    width = 0.35
    
    plt.bar(x - width/2, tempos_serial, width, label='Serial (NumPy)', 
            color='#FF6B6B', alpha=0.8, yerr=stds_serial, capsize=5)
    plt.bar(x + width/2, tempos_dist, width, label=f'Distribuído ({num_servers} servidores)', 
            color='#4ECDC4', alpha=0.8, yerr=stds_dist, capsize=5)
    
    plt.xlabel('Tamanho da Matriz (NxN)', fontsize=14, fontweight='bold')
    plt.ylabel('Tempo de Execução (segundos)', fontsize=14, fontweight='bold')
    plt.title('Comparação: Multiplicação Serial vs Distribuída', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xticks(x, [f'{t}×{t}' for t in tamanhos], fontsize=12)
    plt.legend(fontsize=12, loc='upper left')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    filename1 = f"grafico1_comparacao_barras_{timestamp}.png"
    plt.savefig(filename1, dpi=300, bbox_inches='tight')
    print(f"[SALVO] Gráfico 1 (Barras): {filename1}")
    plt.close()
    
    # ========== GRÁFICO 2: Linhas com Destaque ==========
    plt.figure(figsize=(12, 8))
    
    plt.plot(tamanhos, tempos_serial, marker='o', linewidth=3, markersize=10,
             label='Serial (NumPy)', color='#FF6B6B')
    plt.plot(tamanhos, tempos_dist, marker='s', linewidth=3, markersize=10,
             label=f'Distribuído ({num_servers} servidores)', color='#4ECDC4')
    
    # Preenche área entre as curvas
    plt.fill_between(tamanhos, tempos_serial, tempos_dist, 
                     alpha=0.2, color='green', 
                     label='Ganho de Desempenho')
    
    plt.xlabel('Tamanho da Matriz (NxN)', fontsize=14, fontweight='bold')
    plt.ylabel('Tempo de Execução (segundos)', fontsize=14, fontweight='bold')
    plt.title('Evolução do Tempo: Serial vs Distribuído', 
              fontsize=16, fontweight='bold', pad=20)
    plt.legend(fontsize=12, loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    filename2 = f"grafico2_evolucao_tempo_{timestamp}.png"
    plt.savefig(filename2, dpi=300, bbox_inches='tight')
    print(f"[SALVO] Gráfico 2 (Linhas): {filename2}")
    plt.close()
    
    # ========== GRÁFICO 3: Speedup com Análise ==========
    plt.figure(figsize=(12, 8))
    
    cores = ['#FF6B6B' if s < 1 else '#95E1D3' if s < num_servers else '#4ECDC4' 
             for s in speedups]
    
    plt.bar(range(len(tamanhos)), speedups, color=cores, alpha=0.8, edgecolor='black', linewidth=2)
    plt.axhline(y=1.0, color='red', linestyle='--', linewidth=2, 
                label='Sem ganho (Speedup = 1.0)')
    plt.axhline(y=num_servers, color='green', linestyle='--', linewidth=2,
                label=f'Speedup Ideal ({num_servers}x)')
    
    # Adiciona valores sobre as barras
    for i, (tam, sp) in enumerate(zip(tamanhos, speedups)):
        plt.text(i, sp + 0.1, f'{sp:.2f}x', ha='center', va='bottom', 
                fontweight='bold', fontsize=11)
    
    plt.xlabel('Tamanho da Matriz (NxN)', fontsize=14, fontweight='bold')
    plt.ylabel('Speedup (Serial / Distribuído)', fontsize=14, fontweight='bold')
    plt.title('Análise de Speedup: Quanto Mais Rápido é o Distribuído?', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xticks(range(len(tamanhos)), [f'{t}×{t}' for t in tamanhos], fontsize=12)
    plt.legend(fontsize=12, loc='upper left')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    filename3 = f"grafico3_speedup_{timestamp}.png"
    plt.savefig(filename3, dpi=300, bbox_inches='tight')
    print(f"[SALVO] Gráfico 3 (Speedup): {filename3}")
    plt.close()
    
    # ========== GRÁFICO 4: Escala Logarítmica ==========
    plt.figure(figsize=(12, 8))
    
    plt.loglog(tamanhos, tempos_serial, marker='o', linewidth=3, markersize=10,
               label='Serial (NumPy)', color='#FF6B6B')
    plt.loglog(tamanhos, tempos_dist, marker='s', linewidth=3, markersize=10,
               label=f'Distribuído ({num_servers} servidores)', color='#4ECDC4')
    
    plt.xlabel('Tamanho da Matriz (NxN) - Escala Log', fontsize=14, fontweight='bold')
    plt.ylabel('Tempo de Execução (segundos) - Escala Log', fontsize=14, fontweight='bold')
    plt.title('Análise de Complexidade: Log-Log', 
              fontsize=16, fontweight='bold', pad=20)
    plt.legend(fontsize=12, loc='upper left')
    plt.grid(True, alpha=0.3, which='both')
    plt.tight_layout()
    
    filename4 = f"grafico4_loglog_{timestamp}.png"
    plt.savefig(filename4, dpi=300, bbox_inches='tight')
    print(f"[SALVO] Gráfico 4 (Log-Log): {filename4}")
    plt.close()
    
    # ========== GRÁFICO 5: Eficiência ==========
    plt.figure(figsize=(12, 8))
    
    eficiencias = [(sp / num_servers * 100) for sp in speedups]
    
    cores_ef = ['#FF6B6B' if e < 50 else '#FFE66D' if e < 80 else '#4ECDC4' 
                for e in eficiencias]
    
    plt.bar(range(len(tamanhos)), eficiencias, color=cores_ef, alpha=0.8, 
            edgecolor='black', linewidth=2)
    plt.axhline(y=100, color='green', linestyle='--', linewidth=2,
                label='Eficiência Ideal (100%)')
    
    # Adiciona valores sobre as barras
    for i, (tam, ef) in enumerate(zip(tamanhos, eficiencias)):
        plt.text(i, ef + 2, f'{ef:.1f}%', ha='center', va='bottom',
                fontweight='bold', fontsize=11)
    
    plt.xlabel('Tamanho da Matriz (NxN)', fontsize=14, fontweight='bold')
    plt.ylabel('Eficiência (%)', fontsize=14, fontweight='bold')
    plt.title(f'Eficiência do Sistema Distribuído ({num_servers} servidores)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xticks(range(len(tamanhos)), [f'{t}×{t}' for t in tamanhos], fontsize=12)
    plt.legend(fontsize=12, loc='upper right')
    plt.ylim(0, 120)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    filename5 = f"grafico5_eficiencia_{timestamp}.png"
    plt.savefig(filename5, dpi=300, bbox_inches='tight')
    print(f"[SALVO] Gráfico 5 (Eficiência): {filename5}")
    plt.close()
    
    # ========== GRÁFICO 6: Tabela de Resultados Comparativos ==========
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('tight')
    ax.axis('off')
    
    table_data = [['Tamanho', 'Serial', 'Distribuído', 'Speedup', 'Eficiência', 'Melhor']]
    
    for r in resultados:
        tam = f"{r['tamanho']}×{r['tamanho']}"
        t_ser = f"{r['tempo_medio_serial']:.4f}s"
        t_dist = f"{r['tempo_medio_distribuido']:.4f}s"
        sp = f"{r['speedup']:.2f}x"
        ef = f"{(r['speedup']/num_servers*100):.1f}%"
        melhor = "Dist." if r['speedup'] > 1 else "Serial"
        
        table_data.append([tam, t_ser, t_dist, sp, ef, melhor])
    
    table = ax.table(cellText=table_data, cellLoc='center',
                     loc='center', colWidths=[0.15, 0.18, 0.18, 0.15, 0.17, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 3)
    
    # Estiliza cabeçalho
    for i in range(6):
        table[(0, i)].set_facecolor('#2C3E50')
        table[(0, i)].set_text_props(weight='bold', color='white', fontsize=13)
    
    # Estiliza linhas alternadas
    for i in range(1, len(table_data)):
        for j in range(6):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ECF0F1')
            
            # Destaca coluna "Melhor"
            if j == 5:
                if table_data[i][j] == "Dist.":
                    table[(i, j)].set_facecolor('#A8E6CF')
                else:
                    table[(i, j)].set_facecolor('#FFB3BA')
    
    plt.title('Tabela Comparativa: Serial vs Distribuído', 
              fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    
    filename6 = f"grafico6_tabela_{timestamp}.png"
    plt.savefig(filename6, dpi=300, bbox_inches='tight')
    print(f"[SALVO] Gráfico 6 (Tabela): {filename6}")
    plt.close()
    
    # Resumo final
    print("\n" + "="*70)
    print("  RESUMO DA ANÁLISE")
    print("="*70)
    print(f"\nTamanhos testados: {len(tamanhos)}")
    print(f"Servidores utilizados: {num_servers}")
    print(f"\nPonto de Break-even (onde distribuído fica mais rápido):")
    
    for i, r in enumerate(resultados):
        if r['speedup'] > 1.0:
            print(f"  → A partir de matrizes {r['tamanho']}×{r['tamanho']}")
            break
    else:
        print(f"  → Distribuído não foi mais rápido em nenhum tamanho testado")
    
    print(f"\nMelhor speedup obtido: {max(speedups):.2f}x")
    print(f"  (em matrizes {resultados[speedups.index(max(speedups))]['tamanho']}×{resultados[speedups.index(max(speedups))]['tamanho']})") 
    
    print(f"\nEficiência média: {np.mean(eficiencias):.1f}%")
    print("\n" + "="*70)


def main():
    """Função principal"""
    print("\n" + "="*70)
    print("  SISTEMA DE MULTIPLICAÇÃO DISTRIBUÍDA DE MATRIZES")
    print("  Trabalho de Computação Paralela e Concorrente - AV3")
    print("="*70)
    
    print("\nEscolha o modo de operação:")
    print("1. Modo Apresentação (demonstração interativa)")
    print("2. Modo Benchmark (testes em massa + gráficos)")
    
    opcao = input("\nOpção: ").strip()
    
    if opcao == '1':
        modo_apresentacao()
    elif opcao == '2':
        modo_benchmark()
    else:
        print("Opção inválida!")

if __name__ == "__main__":
    main()