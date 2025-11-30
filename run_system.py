import subprocess
import sys
import time
import os
import signal

def iniciar_servidores(num_servers=2):
    """Inicia múltiplos servidores em processos separados"""
    processos = []
    
    print(f"\n[SETUP] Iniciando {num_servers} servidores...")
    
    for i in range(num_servers):
        port = 5000 + i
        print(f"  → Servidor {i+1} na porta {port}")
        
        # Inicia servidor em processo separado
        if sys.platform == 'win32':
            processo = subprocess.Popen(
                [sys.executable, 'Server.py', str(port)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            processo = subprocess.Popen(
                [sys.executable, 'Server.py', str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        processos.append(processo)
        time.sleep(0.5)
    
    print(f"[SETUP] {num_servers} servidores iniciados com sucesso!")
    return processos


def encerrar_servidores(processos):
    """Encerra todos os servidores"""
    print("\n[CLEANUP] Encerrando servidores...")
    
    for i, proc in enumerate(processos):
        try:
            proc.terminate()
            proc.wait(timeout=3)
            print(f"  → Servidor {i+1} encerrado")
        except:
            proc.kill()
            print(f"  → Servidor {i+1} forçado a encerrar")
    
    print("[CLEANUP] Todos os servidores encerrados")


def main():
    """Função principal"""
    print("="*70)
    print("  SISTEMA AUTOMATIZADO DE EXECUÇÃO")
    print("  Multiplicação Distribuída de Matrizes")
    print("="*70)
    
    print("\nEste script irá:")
    print("1. Iniciar automaticamente os servidores")
    print("2. Executar o cliente")
    print("3. Encerrar os servidores ao final")
    
    num_servers = int(input("\nQuantos servidores deseja iniciar? (2-4 recomendado): "))
    
    processos = []
    
    try:
        # Inicia servidores
        processos = iniciar_servidores(num_servers)
        
        # Aguarda servidores iniciarem completamente
        print("\n[SETUP] Aguardando servidores iniciarem...")
        time.sleep(2)
        
        # Executa cliente
        print("\n[EXEC] Iniciando cliente...\n")
        print("="*70)
        
        subprocess.run([sys.executable, 'Client.py'])
        
    except KeyboardInterrupt:
        print("\n\n[INTERROMPIDO] Execução cancelada pelo usuário")
    
    except Exception as e:
        print(f"\n[ERRO] {e}")
    
    finally:
        # Sempre encerra os servidores
        if processos:
            encerrar_servidores(processos)
    
    print("\n[FIM] Execução concluída")
    print("="*70)


if __name__ == "__main__":
    main()