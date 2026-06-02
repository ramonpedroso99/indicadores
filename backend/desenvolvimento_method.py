from nicegui import ui
import asyncpg
import asyncio
from datetime import datetime
from conexao import conectar_ao_banco

print(">>> Módulo desenvolvimento_method carregado!")

def conteudo_desenvolvimento():
    async def indicador_soas_meta(mes: int, ano: int):
        conn = await conectar_ao_banco()

        query = f"""
        WITH ordered AS (
            SELECT
                si.id,
                si.soa_id,
                si.soa_status_id,
                si.created,
                LEAD(si.created) OVER (PARTITION BY si.soa_id ORDER BY si.created) AS prox_created,
                LEAD(si.soa_status_id) OVER (PARTITION BY si.soa_id ORDER BY si.created) AS prox_status
            FROM soa_interacoes si
        ),
        base AS (
            SELECT
                s.sequencial,
                o.id AS interacao_id,
                o.created,
                o.prox_created
            FROM ordered o
            JOIN soas s ON s.id = o.soa_id
            WHERE
                o.soa_status_id = 6
                AND s.soa_classificacoes_id = 2
                AND s.cliente_id NOT IN (7, 295)
                AND o.prox_status IN (2,4,8,18)
                AND o.prox_created IS NOT NULL
                AND EXTRACT(YEAR  FROM o.prox_created) = {ano}
                AND EXTRACT(MONTH FROM o.prox_created) = {mes}
        ),
        calc AS (
            SELECT
                b.sequencial,
                b.interacao_id,
                COALESCE(SUM(
                    EXTRACT(EPOCH FROM (
                        LEAST(b.prox_created, (gs::date + 1)::timestamp)
                        - GREATEST(b.created, gs::timestamp)
                    ))
                ), 0) AS business_seconds
            FROM base b
            JOIN LATERAL generate_series(
                date_trunc('day', b.created)::date,
                date_trunc('day', b.prox_created)::date,
                interval '1 day'
            ) gs ON TRUE
            LEFT JOIN feriados f ON f.data_feriado = gs::date
            WHERE EXTRACT(ISODOW FROM gs)::int BETWEEN 1 AND 5
                AND f.data_feriado IS NULL
            GROUP BY b.sequencial, b.interacao_id
        )
        SELECT
            COUNT(*) AS total_soas,
            SUM(CASE WHEN (business_seconds / 86400.0) <= 15 THEN 1 ELSE 0 END) AS dentro_15_dias,
            SUM(CASE WHEN (business_seconds / 86400.0) > 15 AND (business_seconds / 86400.0) <= 30 THEN 1 ELSE 0 END) AS dentro_30_dias,
            SUM(CASE WHEN (business_seconds / 86400.0) > 30 THEN 1 ELSE 0 END) AS atrasados
        FROM calc;
        """

        query_atrasados = f"""
        WITH ordered AS (
            SELECT
                si.id,
                si.soa_id,
                si.soa_status_id,
                si.created,
                LEAD(si.created) OVER (PARTITION BY si.soa_id ORDER BY si.created) AS prox_created,
                LEAD(si.soa_status_id) OVER (PARTITION BY si.soa_id ORDER BY si.created) AS prox_status
            FROM soa_interacoes si
        ),
        base AS (
            SELECT
                s.sequencial,
                o.id AS interacao_id,
                o.created,
                o.prox_created
            FROM ordered o
            JOIN soas s ON s.id = o.soa_id
            WHERE
                o.soa_status_id = 6
                AND s.soa_classificacoes_id = 2
                AND s.cliente_id NOT IN (7, 295)
                AND o.prox_status IN (2,4,8,18)
                AND o.prox_created IS NOT NULL
                AND EXTRACT(YEAR  FROM o.prox_created) = {ano}
                AND EXTRACT(MONTH FROM o.prox_created) = {mes}
        ),
        calc AS (
            SELECT
                b.sequencial,
                COALESCE(SUM(
                    EXTRACT(EPOCH FROM (
                        LEAST(b.prox_created, (gs::date + 1)::timestamp)
                        - GREATEST(b.created, gs::timestamp)
                    ))
                ), 0) AS business_seconds
            FROM base b
            JOIN LATERAL generate_series(
                date_trunc('day', b.created)::date,
                date_trunc('day', b.prox_created)::date,
                interval '1 day'
            ) gs ON TRUE
            LEFT JOIN feriados f ON f.data_feriado = gs::date
            WHERE EXTRACT(ISODOW FROM gs)::int BETWEEN 1 AND 5
                AND f.data_feriado IS NULL
            GROUP BY b.sequencial
        )
        SELECT sequencial, ROUND((business_seconds / 86400.0)::numeric, 2) AS dias_uteis
        FROM calc
        WHERE (business_seconds / 86400.0) > 30
        ORDER BY dias_uteis DESC;
        """


        resultado1 = await conn.fetchrow(query)
        
        atrasados = await conn.fetch(query_atrasados)

    
        await conn.close()

        if resultado1 is None:
            resultado1 = {'dentro_15_dias': 0, 'dentro_30_dias': 0, 'atrasados': 0}

        return (
            {
            'total_soas': resultado1['total_soas'] or 0,
            'dentro_15_dias': resultado1['dentro_15_dias'] or 0,
            'dentro_30_dias': resultado1['dentro_30_dias'] or 0,
            'atrasados': resultado1['atrasados'] or 0
        },
        atrasados
    )

    ui.label('🔴 Tempo de análise - SOAS de Novidade').classes('font-bold text-lg')
    ui.label('Medição mensal')
    ui.label('Resultado: A meta é 80% dos SOAs de Novidade atentidos em até 15 dias úteis e 100% em 30 dias úteis.')


    with ui.card().classes("p-6 w-[600px] mx-auto mt-10 shadow-lg rounded-2xl"):
        ui.label("📊 Meta - Tempo de Análise de SOAs de Novidade").classes("text-2xl font-bold mb-4 text-center")
    
        ano_input = ui.number(label="Ano", min=2000, max=2100, value=2025)
        mes_input = ui.number(label="Mês", min=1, max=12, value=1)

        resultado_soa_novidade = ui.column().classes("mt-4")

        atrasados_table = ui.table(
            columns=[
                {"name": "sequencial", "label": "SOA", "field": "sequencial", "align": "left"},
                {"name": "dias_uteis", "label": "Dias Úteis", "field": "dias_uteis", "align": "left"},
            ],
            rows=[],
            row_key="sequencial"
        ).classes("w-full")

        async def on_calcular1():
            mes = int(mes_input.value)
            ano = int(ano_input.value)
            dados, atrasados = await indicador_soas_meta(mes, ano)

            resultado_soa_novidade.clear()
            atrasados_table.rows.clear()
            
            total = dados['total_soas'] or 1  # evita divisão por zero
            perc_80 = round(dados['dentro_15_dias'] / total * 100, 2)
            perc_100 = round((dados['dentro_15_dias'] + dados['dentro_30_dias']) / total * 100, 2)

            # Define mensagens de meta
            meta_80_msg = "✅ Meta 80% atingida!" if perc_80 >= 80 else "⚠️ Meta 80% não atingida"
            meta_100_msg = "✅ Meta 100% atingida!" if perc_100 >= 100 else "⚠️ Meta 100% não atingida"

            with resultado_soa_novidade:
                ui.label(f"Total de SOAs: {dados['total_soas']}").classes("font-bold text-lg")
                ui.label(f"Total de SOAs atrasados: {dados['atrasados']}").classes("text-red font-bold text-lg")
                ui.label(f"Percentual 15 dias: {perc_80}% | Percentual >15 dias: {perc_100}%").classes("font-bold text-center text-lg")
                ui.label(f"{meta_80_msg} | {meta_100_msg}").classes("text-lg font-semibold mt-1 text-center")
                

            with resultado_soa_novidade:
                ui.label("📊 Distribuição dos SOAs").classes("text-lg font-semibold mt-4 justify-center")
                ui.echart({
                    'tooltip': {'trigger': 'item'},
                    'color': ['#4CAF50', 'yellow', 'red'],
                    'series': [{
                        'type': 'pie',
                        'radius': '70%',
                        'data': [
                            {'value': dados['dentro_15_dias'], 'name': 'Meta 15 dias'},
                            {'value': dados['dentro_30_dias'], 'name': 'Meta 16-30 dias'},
                            {'value': dados['atrasados'], 'name': 'Atrasados'},
                        ]
                    }]
                }).classes("h-64 w-full")

                ui.label("Lista dos SOAs atrasados").classes("font-bold mx-auto")
            atrasados_table.rows = [
                {"sequencial": soa["sequencial"], "dias_uteis": soa["dias_uteis"]}
                for soa in atrasados
            ]
                
        ui.button("Calcular", on_click=lambda: asyncio.create_task(on_calcular1())).classes("mt-4 bg-blue-600 text-white w-full")


#########################################SOAS DE ERRO###########################################################################################
    
    async def calcular_soas_erro(mes: int, ano: int):
        conn = await asyncpg.connect(
            user='ramonpedroso',
            password='9JnJp&ph7c&bf%b9D*2',
            database='erpv2',
            host='184.72.149.92',
            port=5432
        )

        query = """
        WITH soas_tempo AS (
            SELECT
                S.id AS soa_id,
                SI.created AS primeira_interacao_data,
                (SELECT I.created 
                FROM soa_interacoes I 
                WHERE I.soa_id = SI.soa_id 
                AND I.soa_status_id = 4 
                ORDER BY I.created ASC
                LIMIT 1) AS proxima_interacao_data,
                EXTRACT(EPOCH FROM (
                    (SELECT I.created 
                    FROM soa_interacoes I 
                    WHERE I.soa_id = SI.soa_id 
                    AND I.soa_status_id = 4 
                    ORDER BY I.created ASC
                    LIMIT 1) - SI.created
                )) / 3600 AS horas_analise
            FROM soa_interacoes SI
            LEFT JOIN soas S ON S.id = SI.soa_id
            WHERE S.soa_classificacoes_id = 4
            AND S.soa_criticidade_id = 3
            AND EXTRACT(MONTH FROM S.data_conclusao) = $1
            AND EXTRACT(YEAR FROM S.data_conclusao) = $2
            AND SI.id = (SELECT I.id 
                        FROM soa_interacoes I 
                        WHERE I.soa_id = SI.soa_id
                            AND I.soa_classificacoes_id = 4
                        ORDER BY I.created DESC
                        LIMIT 1)
        )
        SELECT
            COUNT(*) AS total_soas,
            COUNT(CASE WHEN horas_analise <= 72 THEN 1 END) AS dentro_72h,
            COUNT(CASE WHEN horas_analise > 72 AND horas_analise <= 104 THEN 1 END) AS entre_72_e_104h,
            COUNT(CASE WHEN horas_analise > 104 THEN 1 END) AS fora_104h,
            ROUND(100.0 * COUNT(CASE WHEN horas_analise <= 72 THEN 1 END)/COUNT(*), 2) AS perc_dentro_72h,
            ROUND(100.0 * COUNT(CASE WHEN horas_analise <= 104 THEN 1 END)/COUNT(*), 2) AS perc_dentro_104h
        FROM soas_tempo;
        """

        query_atrasados = """
        WITH soas_tempo AS (
        SELECT
        S.id AS soa_id,
        S.sequencial AS sequencial_soa,
        SI.created AS primeira_interacao_data,
        (SELECT I.created 
        FROM soa_interacoes I 
        WHERE I.soa_id = SI.soa_id 
        AND I.soa_status_id = 4 
        ORDER BY I.created ASC
        LIMIT 1) AS proxima_interacao_data,
        EXTRACT(EPOCH FROM (
            (SELECT I.created 
            FROM soa_interacoes I 
            WHERE I.soa_id = SI.soa_id 
            AND I.soa_status_id = 4 
            ORDER BY I.created ASC
            LIMIT 1) - SI.created
        )) / 3600 AS horas_analise
        FROM soa_interacoes SI
        LEFT JOIN soas S ON S.id = SI.soa_id
        WHERE S.soa_classificacoes_id = 4
        AND S.soa_criticidade_id = 3
        AND EXTRACT(MONTH FROM S.data_conclusao) = $1
        AND EXTRACT(YEAR FROM S.data_conclusao) = $2
        AND SI.id = (
        SELECT I.id 
        FROM soa_interacoes I 
        WHERE I.soa_id = SI.soa_id
            AND I.soa_classificacoes_id = 4
        ORDER BY I.created DESC
        LIMIT 1
            )
        )
        SELECT
            soa_id,
            sequencial_soa,
            primeira_interacao_data,
            proxima_interacao_data,
            horas_analise
        FROM soas_tempo
        WHERE horas_analise > 104
        ORDER BY primeira_interacao_data ASC;
        """

        

        resultado = await conn.fetchrow(query, mes, ano)
        atrasados = await conn.fetch(query_atrasados, mes, ano)

        await conn.close()
        
        return {
            "totais": resultado,
            "atrasados": atrasados
        }

    ui.label('🔴 Tempo de análise - SOAS de Erro').classes('font-bold text-lg')
    ui.label('Medição mensal')
    ui.label('Resultado: A meta é que analisem 70% dos SOAs em 72 horas úteis (criticidade alta) e 100% em 13 dias úteis.')
    
    
    with ui.card().classes("p-6 w-[600px] mx-auto mt-10 shadow-lg rounded-2xl"):
        ui.label("📊 Meta - Tempo de Análise de SOAs de Erro").classes("text-2xl font-bold mb-4 text-center")

        # Inputs numéricos
        ano1_input = ui.number(label="Ano", value=2025, min=2000, max=2100).classes("w-1/2")
        mes1_input = ui.number(label="Mês", value=8, min=1, max=12).classes("w-1/2")

        # Card para resultados
        with ui.row().classes("w-full justify-center mt-4"):
            resultado_novidade= ui.column().classes("w-full gap-4")
            

        async def on_calcular():
            resultado_novidade.clear()
            dados = await calcular_soas_erro(int(mes1_input.value), int(ano1_input.value))
            totais = dados["totais"]
            soas_atrasados = dados["atrasados"]

            if totais["total_soas"] <= 1:
                with resultado_novidade:
                    ui.label("Nenhum SOA encontrado para este período.").classes("text-lg font-semibold text-center")
                return

            total_ajustado = totais["total_soas"]
            fora_meta = totais['fora_104h']

            # KPIs principais em cards
            with resultado_novidade:
                with ui.row().classes("w-full justify-around"):
                    with ui.card().classes("p-4 bg-green-100 text-center").tight().style("min-width:120px").props("flat"):
                        ui.label(f"{totais['dentro_72h']}").classes("text-2xl font-bold text-green-700")
                        ui.label("≤ 72h")
                    with ui.card().classes("p-4 bg-yellow-100 text-center").tight().style("min-width:120px").props("flat"):
                        ui.label(f"{totais['entre_72_e_104h']}").classes("text-2xl font-bold text-yellow-700")
                        ui.label("72h-104h")
                    with ui.card().classes("p-4 bg-red-100 text-center").tight().style("min-width:120px").props("flat"):
                        ui.label(f"{totais['fora_104h']}").classes("text-2xl font-bold text-red-700")
                        ui.label("≤ 104h")

            # Percentuais
            with resultado_novidade:
                ui.label(f"🟢 SOAs dentro de 72h: {totais['perc_dentro_72h']}%").classes("text-green-700 text-lg")
                ui.label(f"🟡 SOAs dentro de 104h: {totais['perc_dentro_104h']}%").classes("text-yellow-700 text-lg")
                ui.label(f"🔴 SOAs atrasados: {totais['fora_104h']}").classes("text-red-700 text-lg")
                
            # Total de SOAs
            with resultado_novidade:
                ui.label(f"Total de SOAs: {total_ajustado}").classes("text-xl font-bold text-center mt-2")
            
            # Gráfico de pizza
            with resultado_novidade:
                ui.label("📊 Distribuição dos SOAs").classes("text-lg font-semibold mt-4")
                ui.echart({
                    'tooltip': {'trigger': 'item'},
                    'color': ['#4CAF50', 'yellow', 'red'],
                    'series': [{
                        'type': 'pie',
                        'radius': '70%',
                        'data': [
                            {'value': totais['dentro_72h'], 'name': '≤ 72h'},
                            {'value': totais['entre_72_e_104h'], 'name': '72h-104h'},
                            {'value': totais['fora_104h'], 'name': '≤ 104h'},
                        ]
                    }]
                }).classes("h-64 w-full")
            
            if soas_atrasados:
                with resultado_novidade:
                    ui.label("Tabela de SOAs Atrasados").classes("font-bold mx-auto")
                    ui.table(
                        columns=[
                            {"name": "soa_id", "label": "SOA ID", "field": "soa_id"},
                            {"name": "unidade", "label": "Unidade", "field": "unidade"},
                            {"name": "primeira_int", "label": "Primeira Interção", "field": "primeira_int"},
                            {"name": "proxima_int", "label": "Próxima interação", "field": "proxima_int"},
                            {"name": "horas_analise", "label": "Horas análise", "field": "horas_analise"},
                        ],
                        rows=[
                            {
                                "soa_id": s["soa_id"],
                                "unidade": s["sequencial_soa"],
                                "primeira_int": s["primeira_interacao_data"].strftime("%Y-%m-%d %H:%M"),
                                "proxima_int": s["proxima_interacao_data"].strftime("%Y-%m-%d %H:%M"),
                                "horas_analise": round(s["horas_analise"], 2)
                            }
                            for s in soas_atrasados
                        ]
                    ).classes("w-full")
            else:
                with resultado_novidade:
                    ui.label("Nenhum SOA atrasado encontrado neste período.").classes("text-lg font-semibold text-center")
                    
        ui.button("Calcular", on_click=lambda: asyncio.create_task(on_calcular())).classes("mt-4 bg-blue-600 text-white w-full")