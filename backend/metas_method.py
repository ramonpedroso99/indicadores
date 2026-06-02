from nicegui import ui
from conexao import conectar_ao_banco

def conteudo_metas():
    ui.label("🎯 Meta de Atendimento — 80% dos SOAs em até 5 horas").classes("text-2xl font-bold mb-4")

    # 🔽 Seletores de Mês e Ano
    with ui.row().classes('items-center gap-4 mb-4'):
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }

        mes_select = ui.select(meses, value=10, label='Mês')
        ano_select = ui.number(label='Ano', value=2025, min=2020, max=2030)

    # 🔹 Tabela de resultados
    tabela = ui.table(
        columns=[
            {'name': 'funcionario', 'label': 'Funcionário', 'field': 'funcionario', 'align': 'left'},
            {'name': 'total_soas', 'label': 'Total de SOAs', 'field': 'total_soas'},
            {'name': 'soas_no_prazo', 'label': 'No Prazo', 'field': 'soas_no_prazo'},
            {'name': 'soas_fora_prazo', 'label': 'Fora do Prazo', 'field': 'soas_fora_prazo'},
            {'name': 'percentual_meta', 'label': '% Meta', 'field': 'percentual_meta'},
        ],
        rows=[],
        row_key='funcionario',
    ).classes('w-full shadow-lg')

    # 🔁 Função de atualização
    async def atualizar_dados():
        mes = mes_select.value
        ano = ano_select.value

        ui.notify(f"Consultando dados de {meses[mes]} / {ano}...", type='info')

        conn = await conectar_ao_banco()
    
        query = f"""
        WITH interacoes_filtradas AS (
            SELECT
                S.sequencial,
                SI.id AS primeira_interacao_id,
                SI.created AS primeira_interacao_data,
                (
                    SELECT I.created
                    FROM soa_interacoes I
                    WHERE I.soa_id = SI.soa_id AND I.id > SI.id
                    ORDER BY I.created ASC
                    LIMIT 1
                ) AS proxima_interacao_data,
                (
                    SELECT I.id
                    FROM soa_interacoes I
                    WHERE I.soa_id = SI.soa_id AND I.id > SI.id
                    ORDER BY I.created ASC
                    LIMIT 1
                ) AS proxima_interacao_id,
                S.cliente_id,
                CL.nome AS cliente_nome,
                SS.descricao AS status_soa
            FROM soa_interacoes SI
            LEFT JOIN soas S ON S.id = SI.soa_id
            LEFT JOIN clientes CL ON CL.id = S.cliente_id
            LEFT JOIN soa_status SS ON S.soa_status_id = SS.id
            WHERE SI.soa_status_id = 1
            AND EXTRACT(MONTH FROM SI.created) = {mes}
            AND EXTRACT(YEAR FROM SI.created) = {ano}
            AND S.cliente_id NOT IN (7, 295)
        ),
        interacoes_com_horas AS (
            SELECT *,
                calcular_horas_uteis2(primeira_interacao_data, proxima_interacao_data) AS horas_uteis
            FROM interacoes_filtradas
        )
        SELECT
            F.nome AS funcionario,
            COUNT(*) AS total_soas,
            COUNT(*) FILTER (WHERE horas_uteis <= 5) AS soas_no_prazo,
            COUNT(*) FILTER (WHERE horas_uteis > 5) AS soas_fora_prazo,
            ROUND(
                (COUNT(*) FILTER (WHERE horas_uteis <= 5) * 100.0 / NULLIF(COUNT(*), 0)), 2
            ) AS percentual_meta
        FROM interacoes_com_horas IC
        LEFT JOIN soa_interacoes I ON I.id = IC.proxima_interacao_id
        LEFT JOIN funcionarios F ON F.id = I.responsavel_id
        WHERE F.nome IN ('Amanda Sobreiro Meneghetti', 'Barbara Ramanda Soares Gregorio')
        GROUP BY F.nome
        ORDER BY percentual_meta DESC;
        """

        resultados = await conn.fetch(query)
        await conn.close()
        
        

        tabela.rows = [
            {
                'funcionario': r['funcionario'] or 'Desconhecido',
                'total_soas': r['total_soas'],
                'soas_no_prazo': r['soas_no_prazo'],
                'soas_fora_prazo': r['soas_fora_prazo'],
                'percentual_meta': f"{r['percentual_meta']}%"
            }
            for r in resultados
        ]
        
        ui.notify("✅ Dados atualizados com sucesso!", type='positive')
        
    # 🔘 Botão de atualização
    ui.button("🔄 Atualizar", on_click=atualizar_dados).classes('mt-4 bg-blue-500 text-white rounded-lg')
