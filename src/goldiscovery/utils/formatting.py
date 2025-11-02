# Em src/goldiscovery/utils/formatting.py

import pandas as pd
import json
# Define as interfaces que consideramos de gerenciamento
MANAGEMENT_INTERFACES = {'FastEthernet0/1'}


def save_to_excel(list_of_connections: list[dict], filename: str):
    """
    Recebe uma lista de conexões, filtra os links de dados,
    e salva um relatório "centrado no dispositivo" com colunas autoajustadas.
    """
    if not list_of_connections:
        print("AVISO: Nenhuma conexão para salvar no relatório.")
        return

    # --- ETAPA 1: FILTRAR APENAS OS LINKS DE DADOS ---
    data_links_only = []
    for conn in list_of_connections:
        local_if = conn.get('local_interface')
        remote_if = conn.get('remote_port')
        # Mantém apenas os links que NÃO são da rede de gerenciamento
        if local_if not in MANAGEMENT_INTERFACES and remote_if not in MANAGEMENT_INTERFACES:
            data_links_only.append(conn)

    print(
        f"\n>>> Total de conexões CDP encontradas: {len(list_of_connections)}. Filtradas para dados: {len(data_links_only)}.")

    if not data_links_only:
        print("AVISO: Nenhum link de dados encontrado para salvar.")
        return

    # --- ETAPA 2: TRANSFORMAR OS DADOS NO FORMATO DE RELATÓRIO ---

    # Converte a lista de links em um DataFrame do Pandas
    df_links = pd.DataFrame(data_links_only)

    # Agrupa todos os links pelo dispositivo "raiz"
    grouped = df_links.groupby('source_hostname')

    report_rows = []

    print(f"\n>>> Gerando relatório centrado em dispositivo para {len(grouped)} dispositivos...")

    # Itera sobre cada grupo (R1, S1, S2...)
    for source_name, group_data in grouped:
        # Pega a primeira linha do grupo para os dados da "raiz"
        first_row = group_data.iloc[0]

        # 1. Adiciona a linha "Dispositivo Principal" (em negrito no Excel)
        report_rows.append({
            'Conexão': f'Dispositivo Principal: {source_name}',
            'IP': first_row.get('source_ip'),
            'Interface': '',  # Interface fica em branco para a linha principal
            'Dispositivo': '',  # Dispositivo fica em branco
            'Plataforma': first_row.get('source_platform')
        })

        # 2. Adiciona uma linha "Vizinho Conectado" para cada link nesse grupo
        for _, neighbor in group_data.iterrows():
            report_rows.append({
                'Conexão': '  -> Vizinho Conectado:',  # Indentação para clareza
                'IP': neighbor.get('neighbor_ip'),
                'Interface': neighbor.get('local_interface'),  # Interface local do dispositivo raiz
                'Dispositivo': neighbor.get('neighbor_id'),
                'Plataforma': neighbor.get('neighbor_platform')
            })

        # 3. Adiciona uma linha em branco para separar os blocos
        report_rows.append({})

    # --- ETAPA 3: SALVAR O EXCEL COM FORMATAÇÃO ---
    try:
        # Cria o DataFrame final formatado
        df_report = pd.DataFrame(report_rows)

        # Cria um "escritor" de Excel usando o xlsxwriter
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            df_report.to_excel(writer, sheet_name='Topologia', index=False)

            # Pega o objeto da planilha para formatar
            worksheet = writer.sheets['Topologia']

            # Autoajusta a largura das colunas
            for idx, col in enumerate(df_report.columns):
                series = df_report[col]
                max_len = max(
                    (series.astype(str).map(len).max() or 0),  # Comprimento do maior dado
                    len(str(col))  # Comprimento do título da coluna
                ) + 2  # Adiciona uma pequena margem
                worksheet.set_column(idx, idx, max_len)

        print(f"\n✅ Relatório de topologia salvo com sucesso em: {filename}")

    except Exception as e:
        print(f"\n❌ FALHA ao salvar o relatório Excel: {e}")

def save_to_json(data: list[dict], filename: str):
    """
    Salva uma lista de dicionários diretamente em um arquivo JSON formatado.
    """
    print(f"\n>>> Salvando dados brutos em JSON...")
    try:
        with open(filename, 'w') as json_file:
            # indent=4 torna o arquivo JSON legível para humanos
            json.dump(data, json_file, indent=4)
        print(f"✅ Dados JSON salvos com sucesso em: {filename}")
    except Exception as e:
        print(f"\n❌ FALHA ao salvar o relatório JSON: {e}")