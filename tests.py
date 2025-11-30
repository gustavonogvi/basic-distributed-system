
import subprocess
import sys
import time

def teste_rapido():
    """Executa teste rápido do sistema"""
    print("\n" + "="*70)
    print("  TESTE RÁPIDO DO SISTEMA")
    print("  Configuração: 2 servidores, matrizes 4x4")
    print("="*70)
    
    processos_servidores = []
    
    try:
        # Inicia 2 servidores
        print("\n[1/4] Iniciando servidores...")
        
        for i in range(2):
            port = 5000 + i
            if sys.platform == 'win32':
                proc = subprocess.Popen(
                    [sys.executable, 'Server.py', str(port)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                proc = subprocess.Popen(
                    [sys.executable, 'Server.py', str(port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            processos_servidores.append(proc)
            print(f"  ✓ Servidor {i+1} iniciado (porta {port})")
        
        time.sleep(2)
        
        # Testa importações
        print("\n[2/4] Verificando dependências...")
        try:
            import numpy
            print("  ✓ NumPy instalado")
            import matplotlib
            print("  ✓ Matplotlib instalado")
        except ImportError as e:
            print(f"  ✗ Erro: {e}")
            print("\n  Execute: pip install numpy matplotlib")
            return
        
        # Testa conexão
        print("\n[3/4] Testando conectividade...")
        import socket
        
        for i in range(2):
            port = 5000 + i
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(('localhost', port))
                s.close()
                print(f"  ✓ Servidor {i+1} respondendo")
            except:
                print(f"  ✗ Servidor {i+1} não responde")
        
        # Executa teste real
        print("\n[4/4] Executando multiplicação de teste...")
        print("-" * 70)
        
        from client import MatrixClient, multiplicacao_serial
        import numpy as np
        
        servers = [('localhost', 5000), ('localhost', 5001)]
        client = MatrixClient(servers)
        
        # Teste simples
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[5, 6], [7, 8]])
        
        print("\nMatriz A:")
        print(A)
        print("\nMatriz B:")
        print(B)
        
        # Teste Serial
        print("\n[TESTE SERIAL]")
        C_serial, tempo_serial = multiplicacao_serial(A, B)
        print(f"Tempo serial: {tempo_serial:.6f}s")
        
        # Teste Distribuído
        print("\n[TESTE DISTRIBUÍDO]")
        C, tempo_dist = client.distribute_multiplication(A, B, show_details=True)
        
        print("\nMatriz C (resultado):")
        print(C)
        
        # Verifica correção
        if client.verify_result(A, B, C):
            print("\n" + "="*70)
            print("  ✅ TESTE PASSOU! Sistema funcionando corretamente!")
            print("="*70)
            print(f"\n  Comparação de Desempenho:")
            print(f"  - Tempo serial:      {tempo_serial:.6f}s")
            print(f"  - Tempo distribuído: {tempo_dist:.6f}s")
            
            if tempo_dist < tempo_serial:
                print(f"  - Speedup:           {tempo_serial/tempo_dist:.2f}x")
                print(f"  ✓ Distribuído mais rápido!")
            else:
                print(f"  - Slowdown:          {tempo_dist/tempo_serial:.2f}x")
                print(f"  ℹ  Para matrizes 2×2, serial é mais eficiente")
                print(f"     (overhead de comunicação > ganho paralelo)")
            
            print("\n  Próximos passos:")
            print("  1. Execute 'python Client.py' para usar o sistema completo")
            print("  2. No benchmark, teste tamanhos: 10,50,100,200,400,800")
            print("  3. Compare serial vs distribuído nos gráficos!")
            print("  4. Prepare sua apresentação!")
        else:
            print("\n" + "="*70)
            print("  ❌ TESTE FALHOU! Resultado incorreto")
            print("="*70)
        
    except FileNotFoundError:
        print("\n❌ Erro: Arquivos Server.py ou Client.py não encontrados")
        print("   Certifique-se de que todos os arquivos estão no mesmo diretório")
    
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Encerra servidores
        print("\n[CLEANUP] Encerrando servidores...")
        for i, proc in enumerate(processos_servidores):
            try:
                proc.terminate()
                proc.wait(timeout=2)
                print(f"  ✓ Servidor {i+1} encerrado")
            except:
                proc.kill()
        
        print("\n" + "="*70)
        print("  Teste concluído!")
        print("="*70 + "\n")


if __name__ == "__main__":
    teste_rapido()