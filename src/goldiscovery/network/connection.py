# src/goldiscovery/network/connection.py

from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
import yaml
from pprint import pprint
from src.goldiscovery.network.parsers import parse_cdp_neighbors_detail
from src.goldiscovery.utils.formatting import save_to_excel

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


def test_connection():
    """Função para conectar, coletar dados e montar o relatório de conexões."""
    print(">>> Carregando inventário...")
    inventory_data = load_inventory(INVENTORY_FILE)

    if not inventory_data or 'devices' not in inventory_data or not inventory_data['devices']:
        print("Erro: Inventário está vazio ou mal formatado.")
        return

    first_device = inventory_data['devices'][0]
    print(
        f"\n>>> Conectando ao dispositivo semente: {first_device.get('name', 'N/A')} ({first_device.get('host', 'N/A')})")

    try:
        connection_params = first_device.copy()
        connection_params.pop('name', None)

        with ConnectHandler(**connection_params) as net_connect:
            print("✅ SUCESSO! Conexão estabelecida.")
            net_connect.enable()
            prompt = net_connect.find_prompt()
            source_hostname = prompt.strip().strip('#').strip('>')
            print(f"Dispositivo identificado como: '{source_hostname}'")

            print("\n>>> Coletando vizinhos CDP...")
            cdp_output = net_connect.send_command("show cdp neighbors detail")

            # O parser retorna uma lista de vizinhos
            parsed_neighbors = parse_cdp_neighbors_detail(cdp_output)

            # --- LÓGICA PARA COMBINAR DADOS DA RAIZ E DOS VIZINHOS ---
            full_connections = []
            for neighbor in parsed_neighbors:
                connection_data = {
                    'source_hostname': source_hostname,
                    'source_platform': first_device.get('name'),  # Usamos o 'name' do YML como plataforma da raiz
                    'source_ip': first_device.get('host'),
                    'local_interface': neighbor.get('local_interface'),
                    'neighbor_id': neighbor.get('neighbor_id'),
                    'neighbor_ip': neighbor.get('neighbor_ip'),
                    'remote_port': neighbor.get('remote_port'),
                    'neighbor_platform': neighbor.get('neighbor_platform')
                }
                full_connections.append(connection_data)

            print("\n>>> Conexões Completas Descobertas:")
            pprint(full_connections)

            if full_connections:
                save_to_excel(full_connections, "reports/discovery_report.xlsx")

    except Exception as e:
        print(f"\n❌ FALHA! Ocorreu um erro inesperado: {e}")


if __name__ == '__main__':
    test_connection()