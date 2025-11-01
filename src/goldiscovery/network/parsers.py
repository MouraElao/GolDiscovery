# Em src/goldiscovery/network/parsers.py

import re


def parse_cdp_neighbors_detail(cdp_output: str) -> list[dict]:
    """
    Analisa a saída do 'show cdp neighbors detail' e a transforma em uma lista
    de dicionários de vizinhos. Esta versão é mais robusta e trata
    cada campo de informação de forma independente.
    """
    neighbors_list = []
    # Divide a saída em blocos, um para cada vizinho
    device_blocks = cdp_output.strip().split('-------------------------')

    for block in device_blocks:
        if not block.strip():
            continue

        neighbor_data = {}

        # --- LÓGICA DE PARSING ROBUSTA ---
        # Tenta extrair cada pedaço de informação separadamente.

        # 1. Device ID (Obrigatório)
        device_id_match = re.search(r"Device ID: (.*?)\n", block)
        if device_id_match:
            neighbor_data['neighbor_id'] = device_id_match.group(1).strip()
        else:
            continue  # Se não conseguirmos nem o ID, pulamos este bloco

        # 2. IP Address (Opcional, mas crucial para o crawler)
        ip_address_match = re.search(r"IP address: (.*?)\n", block)
        if ip_address_match:
            neighbor_data['neighbor_ip'] = ip_address_match.group(1).strip()

        # 3. Platform (Opcional)
        # Ajustado para não depender da palavra "Capabilities"
        platform_match = re.search(r"Platform: (.*?),", block)
        if platform_match:
            neighbor_data['neighbor_platform'] = platform_match.group(1).strip()

        # 4. Interfaces (Obrigatório para o link)
        interface_match = re.search(r"Interface: (.*?),.*?Port ID \(outgoing port\): (.*?)\n", block)
        if interface_match:
            neighbor_data['local_interface'] = interface_match.group(1).strip()
            neighbor_data['remote_port'] = interface_match.group(2).strip()
        else:
            continue  # Se não sabemos as portas, não é um link válido para o relatório

        # Adiciona à lista
        neighbors_list.append(neighbor_data)

    return neighbors_list