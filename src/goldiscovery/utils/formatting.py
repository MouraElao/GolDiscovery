# Em src/goldiscovery/utils/formatting.py

import pandas as pd

MANAGEMENT_INTERFACES = {'FastEthernet0/1'}

def get_base_hostname(hostname):
    """ Retorna a parte do hostname antes do primeiro ponto (e em minúsculas), ou None. """
    if isinstance(hostname, str):
        return hostname.split('.')[0].lower().strip()
    return None

def save_to_excel(list_of_connections: list[dict], filename: str):
    """
    Recebe uma lista de conexões, filtra dados, remove duplicatas de forma robusta
    e salva no formato de bloco.
    """
    if not list_of_connections:
        print("AVISO: Nenhuma conexão para salvar no relatório.")
        return

    # --- ETAPA 1: FILTRAR APENAS OS LINKS DE DADOS ---
    data_links_only = []
    for conn in list_of_connections:
        # Verifica se AMBAS as interfaces NÃO são de gerenciamento
        local_if = conn.get('local_interface')
        remote_if = conn.get('remote_port')
        if local_if not in MANAGEMENT_INTERFACES and remote_if not in MANAGEMENT_INTERFACES:
            data_links_only.append(conn)
        else:
            # Opcional: Log para ver quais links foram ignorados
            # print(f"DEBUG: Ignorando link de gerenciamento: {conn.get('source_hostname')}({local_if}) <-> {conn.get('neighbor_id')}({remote_if})")
            pass

    print(f"\n>>> Total de conexões CDP encontradas: {len(list_of_connections)}. Filtradas para dados: {len(data_links_only)}.")

    # --- ETAPA 2: LIMPEZA DE DUPLICATAS (Refinada) ---
    seen_links_identifiers = set()
    unique_data_links_final = []

    print(f"\n>>> Processando {len(data_links_only)} links de dados para gerar relatório único...")

    for link in data_links_only:
        # Usa a função auxiliar para pegar os nomes base e em minúsculas
        hostname_a = get_base_hostname(link.get('source_hostname'))
        hostname_b = get_base_hostname(link.get('neighbor_id'))

        # Garante que temos ambos os nomes antes de criar o identificador
        if hostname_a and hostname_b:
            # Cria o identificador ordenado (garante A->B == B->A)
            link_identifier = tuple(sorted((hostname_a, hostname_b)))

            # SÓ adiciona à lista final se o link físico ainda não foi visto
            if link_identifier not in seen_links_identifiers:
                unique_data_links_final.append(link)
                seen_links_identifiers.add(link_identifier)
        else:
            print(f"AVISO: Link ignorado na limpeza por falta de nome de dispositivo: {link}")

    print(f"\n>>> Total de links únicos reportados no Excel: {len(unique_data_links_final)}.")

    # --- ETAPA 3: FORMATAÇÃO DO RELATÓRIO ---
    try:
        report_rows = []

        if not unique_data_links_final:
             print("AVISO: Nenhum link de dados único encontrado para salvar.")
             return

        # Itera sobre os links ÚNICOS FINAIS
        for connection in unique_data_links_final:
            source_row = {
                'Conexão': 'Dispositivo Raiz',
                'IP': connection.get('source_ip'),
                'Interface': connection.get('local_interface'),
                'Dispositivo': connection.get('source_hostname'), # Mantém o nome original no relatório
                'Plataforma': connection.get('source_platform')
            }
            report_rows.append(source_row)

            neighbor_row = {
                'Conexão': 'Vizinho Conectado',
                'IP': connection.get('neighbor_ip'),
                'Interface': connection.get('remote_port'),
                'Dispositivo': connection.get('neighbor_id'), # Mantém o nome original no relatório
                'Plataforma': connection.get('neighbor_platform')
            }
            report_rows.append(neighbor_row)

            blank_row = {}
            report_rows.append(blank_row)

        df = pd.DataFrame(report_rows)

        df.to_excel(filename, index=False)
        print(f"\n✅ Relatório de conexões salvo com sucesso em: {filename}")

    except Exception as e:
        print(f"\n❌ FALHA ao salvar o relatório Excel: {e}")