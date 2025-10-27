# Em src/goldiscovery/core/discovery.py

import yaml
from pprint import pprint
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
from src.goldiscovery.network.parsers import parse_cdp_neighbors_detail
from src.goldiscovery.utils.formatting import save_to_excel

# O caminho para o inventário, lido a partir da raiz do projeto
INVENTORY_FILE = "config/inventory.yml"


def load_inventory(file_path):
    """Carrega o inventário de dispositivos do arquivo YAML."""
    try:
        with open(file_path, 'r') as file:
            inventory = yaml.safe_load(file)
        return inventory
    except FileNotFoundError:
        print(f"Erro: Arquivo de inventário não encontrado em '{file_path}'")
        return None


def start_discovery():
    """Função principal que orquestra todo o processo de descoberta da rede."""
    print("--- INICIANDO PROCESSO DE DESCOBERTA DE REDE ---")

    # 1. INICIALIZAÇÃO
    inventory = load_inventory(INVENTORY_FILE)
    if not inventory or 'devices' not in inventory:
        print("Erro: Falha ao carregar o inventário. Verifique o 'config/inventory.yml'")
        return

    # Usaremos o primeiro dispositivo do YML como credencial padrão para todos
    default_creds = inventory['devices'][0]

    devices_to_visit = []  # Fila de dispositivos para visitar
    devices_visited = set()  # Conjunto de IPs que já visitamos (para evitar loops)
    all_discovered_connections = []  # Lista mestre de todos os links encontrados

    # Adiciona os dispositivos "semente" do inventário na fila
    for device in inventory['devices']:
        devices_to_visit.append(device)

    # 2. O LOOP DE DESCOBERTA
    while devices_to_visit:
        # Pega o próximo dispositivo da fila
        current_device = devices_to_visit.pop(0)
        current_host = current_device.get('host')

        print(f"\n>>> Processando dispositivo: {current_device.get('name')} ({current_host})")

        # Evita loops, pulando dispositivos que já foram processados
        if current_host in devices_visited:
            print(f"--- Dispositivo {current_host} já visitado. Pulando.")
            continue

        try:
            # 3. CONEXÃO
            connection_params = current_device.copy()
            connection_params.pop('name', None)

            with ConnectHandler(**connection_params) as net_connect:
                print(f"✅ Conexão com {current_host} estabelecida.")
                net_connect.enable()
                prompt = net_connect.find_prompt()
                source_hostname = prompt.strip().strip('#').strip('>')
                print(f"Dispositivo identificado como: '{source_hostname}'")

                devices_visited.add(current_host)  # Marca como visitado

                # 4. COLETA E PROCESSAMENTO
                cdp_output = net_connect.send_command("show cdp neighbors detail")

                # O parser retorna uma lista de dicionários de vizinhos
                parsed_neighbors = parse_cdp_neighbors_detail(cdp_output)

                # 5. REGISTRO E EXPANSÃO DA BUSCA
                for neighbor in parsed_neighbors:
                    # Monta o dicionário de conexão completo
                    connection_data = {
                        'source_hostname': source_hostname,
                        'source_platform': current_device.get('name'),  # Plataforma da Raiz
                        'source_ip': current_host,
                        'local_interface': neighbor.get('local_interface'),
                        'neighbor_id': neighbor.get('neighbor_id'),
                        'neighbor_ip': neighbor.get('neighbor_ip'),
                        'remote_port': neighbor.get('remote_port'),
                        'neighbor_platform': neighbor.get('neighbor_platform')
                    }
                    all_discovered_connections.append(connection_data)

                    # Adiciona o vizinho à fila para ser visitado, se ele tiver um IP
                    neighbor_ip = neighbor.get('neighbor_ip')
                    if neighbor_ip and neighbor_ip not in devices_visited:
                        print(
                            f"--- Novo vizinho encontrado: {neighbor.get('neighbor_id')} ({neighbor_ip}). Adicionando à fila.")
                        # Cria um novo "trabalho" para o vizinho, usando as credenciais padrão
                        new_device_to_visit = default_creds.copy()
                        new_device_to_visit['host'] = neighbor_ip
                        new_device_to_visit['name'] = neighbor.get('neighbor_id')
                        devices_to_visit.append(new_device_to_visit)

        except (NetmikoAuthenticationException, NetmikoTimeoutException, Exception) as e:
            print(f"❌ FALHA ao processar o dispositivo {current_host}: {e}")
            devices_visited.add(current_host)  # Marca como visitado para não tentar de novo
            continue  # Pula para o próximo dispositivo da fila

    # 6. FINALIZAÇÃO
    print("\n--- PROCESSO DE DESCOBERTA CONCLUÍDO ---")
    print(f"Total de dispositivos visitados: {len(devices_visited)}")
    print(f"Total de conexões encontradas: {len(all_discovered_connections)}")

    if all_discovered_connections:
        save_to_excel(all_discovered_connections, "reports/discovery_report_COMPLETO.xlsx")
    else:
        print("Nenhuma conexão foi descoberta.")