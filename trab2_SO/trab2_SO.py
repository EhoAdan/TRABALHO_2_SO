import random
import math

# -------------------------------------------------------------------
# TRABALHO 2: GERENCIAMENTO DE MEMÓRIA COM PAGINAÇÃO
#
# As configurações (PHYSICAL_MEMORY_SIZE, PAGE_SIZE, MAX_PROCESS_SIZE)
# serão solicitadas ao usuário no início da execução.
# -------------------------------------------------------------------

class Process:
    """
    Representa um processo com sua memória lógica e tabela de páginas.
    """
    def __init__(self, pid, size):
        self.pid = pid
        self.size = size
        # Tabela de páginas: Mapeia (Página Lógica -> Quadro Físico)
        # Ex: { 0: 5, 1: 10, 2: 1 }
        self.page_table = {}
        # A memória lógica é inicializada com valores aleatórios,
        # conforme solicitado.
        try:
            self.logical_memory = bytearray(random.getrandbits(8) for _ in range(size))
        except MemoryError:
            print(f"Alerta: Falha ao alocar {size} bytes para memória lógica do processo {pid}.")
            self.logical_memory = bytearray(size)

class MemoryManager:
    """
    Gerencia a memória física, a lista de quadros livres e os processos.
    """
    def __init__(self, physical_size, page_size, max_proc_size):
        # 1. Configurações
        self.physical_size = physical_size
        self.page_size = page_size
        self.max_process_size = max_proc_size
        # Calcula o número total de quadros na memória física
        self.total_frames = physical_size // page_size
        # 2. Representação da Memória Física
        self.physical_memory = bytearray(self.physical_size)
        # 3. Estrutura de Quadros Livres
        self.free_frames = list(range(self.total_frames - 1, -1, -1))
        # 4. Lista de Processos
        self.processes = {}

    def view_memory(self):
        """
        Exibe o estado atual da memória física, quadro a quadro.
        """
        print("\n--- 👁️ Visualização da Memória Física ---")
        free_count = len(self.free_frames)
        used_count = self.total_frames - free_count
        free_perc = (free_count / self.total_frames) * 100
        print(f"Memória Livre: {free_count}/{self.total_frames} quadros ({free_perc:.2f}%)")
        print(f"Memória Usada: {used_count}/{self.total_frames} quadros")
        print("-" * 40)
        frame_map = {}
        for pid, process in self.processes.items():
            for page, frame in process.page_table.items():
                frame_map[frame] = (pid, page)
        for frame in range(self.total_frames):
            frame_start = frame * self.page_size
            frame_data_snippet = self.physical_memory[frame_start:frame_start + 8].hex(" ")
            if frame in frame_map:
                pid, page = frame_map[frame]
                print(f"Quadro {frame:02d}: [Processo {pid}, Página {page}] | Início: {frame_data_snippet}...")
            else:
                print(f"Quadro {frame:02d}: [LIVRE] | Início: {frame_data_snippet}...")
        print("------------------------------------------")

    def create_process(self, pid, size):
        """
        Tenta criar e alocar memória para um novo processo.
        """
        if pid in self.processes:
            return f"❌ Erro: Processo com PID {pid} já existe."
        if size <= 0:
            return "❌ Erro: Tamanho do processo deve ser positivo."
        if size > self.max_process_size:
            return f"❌ Erro: Tamanho {size} bytes excede o máximo de {self.max_process_size} bytes."
        num_pages_needed = math.ceil(size / self.page_size)
        if num_pages_needed > len(self.free_frames):
            return f"❌ Erro: Memória insuficiente. Requer {num_pages_needed} quadros, mas apenas {len(self.free_frames)} estão livres."
        print(f"Alocando {num_pages_needed} páginas para o Processo {pid}...")
        new_process = Process(pid, size)
        allocated_frames = []
        for page_number in range(num_pages_needed):
            frame_number = self.free_frames.pop()
            allocated_frames.append(frame_number)
            new_process.page_table[page_number] = frame_number
            logical_start = page_number * self.page_size
            logical_end = min(logical_start + self.page_size, size)
            page_data = new_process.logical_memory[logical_start:logical_end]
            physical_start = frame_number * self.page_size
            self.physical_memory[physical_start:physical_start + self.page_size] = b'\x00' * self.page_size
            self.physical_memory[physical_start:physical_start + len(page_data)] = page_data
        self.processes[pid] = new_process
        return f"✅ Sucesso: Processo {pid} ({size} bytes) criado e alocado em {num_pages_needed} quadros (Quadros: {allocated_frames})."

    def view_page_table(self, pid):
        """
        Exibe a tabela de páginas de um processo específico.
        """
        process = self.processes.get(pid)
        if not process:
            print(f"❌ Erro: Processo {pid} não encontrado.")
            return
        print(f"\n--- 📄 Tabela de Páginas do Processo {pid} ---")
        print(f"Tamanho Total: {process.size} bytes")
        print(f"Páginas Alocadas: {len(process.page_table)}")
        print("Mapeamento (Página -> Quadro):")
        if not process.page_table:
            print(" (O processo não possui páginas alocadas)")
            return
        sorted_pages = sorted(process.page_table.keys())
        for page in sorted_pages:
            frame = process.page_table[page]
            print(f" Página {page:02d} -> Quadro {frame:02d}")
        print("------------------------------------------")

# --- FUNÇÕES AUXILIARES PARA A NOVA LÓGICA DE CONFIGURAÇÃO ---

def is_power_of_two(n):
    """Verifica se um número é uma potência de dois."""
    if n <= 0:
        return False
    # Truque de bits: uma potência de 2 (ex: 8 = 1000) e
    # ela menos 1 (ex: 7 = 0111) não têm bits '1' em comum.
    # 1000 & 0111 = 0000
    return (n & (n - 1)) == 0

def get_validated_input(prompt_message, must_be_power_of_two=True):
    """
    Solicita um input numérico ao usuário, validando se é positivo
    e (opcionalmente) se é uma potência de dois.
    """
    while True:
        try:
            value_str = input(prompt_message)
            value = int(value_str)
            if value <= 0:
                print("❌ Erro: O valor deve ser um inteiro positivo.")
                continue
            if must_be_power_of_two and not is_power_of_two(value):
                print(f"❌ Erro: O valor ({value}) deve ser uma potência de dois (ex: 2, 4, 1024, 4096).")
                continue
            return value
        except ValueError:
            print("❌ Erro: Entrada inválida. Digite um número inteiro.")

# --- FUNÇÃO PRINCIPAL MODIFICADA ---

def main_loop():
    """
    Interface principal do simulador por linha de comando.
    Agora solicita a configuração inicial.
    """
    print("--- 🚀 Simulador de Gerenciamento de Memória com Paginação ---")
    print("\nBem-vindo! Por favor, defina as configurações do simulador.")
    print("Nota: Os tamanhos de memória e página devem ser potências de 2.")
    
    # Solicita as configurações ao usuário
    physical_memory_size = get_validated_input(" Tamanho da Memória Física (bytes, ex: 65536): ")
    page_size = get_validated_input(" Tamanho da Página/Quadro (bytes, ex: 4096): ")
    
    # Validação extra: página não pode ser maior que a memória
    while page_size > physical_memory_size:
        print("❌ Erro: O tamanho da página não pode ser maior que a memória física.")
        page_size = get_validated_input(" Tamanho da Página/Quadro (bytes, ex: 4096): ")
    
    # O tamanho máximo do processo não precisa ser potência de 2,
    # mas o enunciado original sugere que sim. Vamos manter essa regra.
    max_process_size = get_validated_input(" Tamanho Máximo de um Processo (bytes, ex: 16384): ")
    total_frames = physical_memory_size // page_size
    
    print("\nConfiguração Inicial Definida:")
    print(f" Memória Física: {physical_memory_size} bytes")
    print(f" Tamanho Página/Quadro: {page_size} bytes")
    print(f" Tamanho Máx. Processo: {max_process_size} bytes")
    print(f" Total de Quadros Físicos: {total_frames}")
    print("----------------------------------------------------------")
    
    # Inicializa o gerenciador COM OS VALORES FORNECIDOS
    manager = MemoryManager(physical_memory_size, page_size, max_process_size)
    
    while True:
        print("\nOpções:")
        print(" 1. Visualizar Memória Física")
        print(" 2. Criar Processo")
        print(" 3. Visualizar Tabela de Páginas de um Processo")
        print(" 4. Sair")
        choice = input("Escolha uma opção (1-4): ")
        
        if choice == '1':
            manager.view_memory()
        elif choice == '2':
            try:
                pid = int(input(" Digite o ID do processo (ex: 101): "))
                # Usa a variável 'max_process_size' na mensagem
                size_str = input(f" Digite o tamanho do processo em bytes (max {max_process_size}): ")
                if 'k' in size_str.lower():
                    size = int(size_str.lower().replace('k', '')) * 1024
                else:
                    size = int(size_str)
                message = manager.create_process(pid, size)
                print(message)
            except ValueError:
                print("❌ Erro: ID e tamanho devem ser números inteiros.")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
        elif choice == '3':
            try:
                pid = int(input(" Digite o ID do processo (ex: 101): "))
                manager.view_page_table(pid)
            except ValueError:
                print("❌ Erro: ID deve ser um número inteiro.")
        elif choice == '4':
            print("Saindo do simulador... Até logo! 👋")
            break
        else:
            print("Opção inválida. Tente novamente.")

# Ponto de entrada do programa
if __name__ == "__main__":
    main_loop()
