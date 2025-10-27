# Em src/goldiscovery/network/parsers.py

import re


def parse_cdp_neighbors_detail(cdp_output: str) -> list[dict]:
    """
    Analisa a saída do 'show cdp neighbors detail' e a transforma em uma lista
    de dicionários, onde cada dicionário contém os detalhes de um vizinho.
    """
    neighbors_list = []
    device_blocks = cdp_output.strip().split('-------------------------')

    for block in device_blocks:
        if not block.strip():
            continue

        neighbor_data = {}

        # Usando Regex para extrair cada pedaço de informação do vizinho
        device_id_match = re.search(r"Device ID: (.*?)\n", block)
        ip_address_match = re.search(r"IP address: (.*?)\n", block)
        platform_match = re.search(r"Platform: (.*?),", block)  # Ajustado para pegar apenas a plataforma
        interface_match = re.search(r"Interface: (.*?),.*?Port ID \(outgoing port\): (.*?)\n", block)

        if device_id_match:
            neighbor_data['neighbor_id'] = device_id_match.group(1).strip()
        if ip_address_match:
            neighbor_data['neighbor_ip'] = ip_address_match.group(1).strip()
        if platform_match:
            neighbor_data['neighbor_platform'] = platform_match.group(1).strip()
        if interface_match:
            neighbor_data['local_interface'] = interface_match.group(1).strip()
            neighbor_data['remote_port'] = interface_match.group(2).strip()

        if 'neighbor_id' in neighbor_data:
            neighbors_list.append(neighbor_data)

    return neighbors_list