# Em src/goldiscovery/utils/formatting.py

import pandas as pd


def save_to_excel(list_of_connections: list[dict], filename: str):
    """
    Recebe uma lista de dicionários de conexões e a salva em um arquivo Excel
    com o formato de 'bloco de conexão' (Raiz + Vizinho).
    """
    if not list_of_connections:
        print("AVISO: Nenhuma conexão para salvar no relatório.")
        return

    try:
        report_rows = []

        # Para cada conexão encontrada, criamos o bloco de 2 linhas no relatório
        for connection in list_of_connections:
            # 1. A linha da "Raiz"
            source_row = {
                'Conexão': 'Dispositivo Raiz',
                'IP': connection.get('source_ip'),
                'Interface': connection.get('local_interface'),
                'Dispositivo': connection.get('source_hostname'),
                'Plataforma': connection.get('source_platform')
            }
            report_rows.append(source_row)

            # 2. A linha do "Vizinho"
            neighbor_row = {
                'Conexão': 'Vizinho Conectado',
                'IP': connection.get('neighbor_ip'),
                'Interface': connection.get('remote_port'),
                'Dispositivo': connection.get('neighbor_id'),
                'Plataforma': connection.get('neighbor_platform')
            }
            report_rows.append(neighbor_row)

            # 3. Uma linha em branco para separar visualmente as conexões (opcional)
            blank_row = {}
            report_rows.append(blank_row)

        # Criamos o DataFrame a partir da nossa lista de linhas formatadas
        df = pd.DataFrame(report_rows)

        df.to_excel(filename, index=False)
        print(f"\n✅ Relatório de conexões salvo com sucesso em: {filename}")

    except Exception as e:
        print(f"\n❌ FALHA ao salvar o relatório Excel: {e}")