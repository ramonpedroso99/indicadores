from nicegui import ui
import asyncpg
import asyncio
from datetime import datetime, date
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


        try:
            resultado1 = await conn.fetchrow(query)
            atrasados  = await conn.fetch(query_atrasados)
        finally:
            await conn.close()

        if resultado1 is None:
            resultado1 = {'total_soas': 0, 'dentro_15_dias': 0, 'dentro_30_dias': 0, 'atrasados': 0}

        return (
            {
                'total_soas':     resultado1['total_soas']     or 0,
                'dentro_15_dias': resultado1['dentro_15_dias'] or 0,
                'dentro_30_dias': resultado1['dentro_30_dias'] or 0,
                'atrasados':      resultado1['atrasados']      or 0,
            },
            atrasados,
        )

    ui.label('🔴 Tempo de análise - SOAS de Novidade').classes('font-bold text-lg')
    ui.label('Medição mensal')
    ui.label('Resultado: A meta é 80% dos SOAs de Novidade atentidos em até 15 dias úteis e 100% em 30 dias úteis.')


    with ui.card().classes("p-6 w-[600px] mx-auto mt-10 shadow-lg rounded-2xl"):
        ui.label("📊 Meta - Tempo de Análise de SOAs de Novidade").classes("text-2xl font-bold mb-4 text-center")
    
        ano_input = ui.number(label="Ano", min=2000, max=2100, value=2025)
        mes_input = ui.number(label="Mês", min=1, max=12, value=1)

        spinner_novidade = ui.spinner('dots', size='lg').classes('mx-auto mt-2')
        spinner_novidade.set_visibility(False)
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
            spinner_novidade.set_visibility(True)
            try:
                dados, atrasados = await indicador_soas_meta(mes, ano)
            except Exception as e:
                spinner_novidade.set_visibility(False)
                with resultado_soa_novidade:
                    ui.label(f"❌ Erro: {e}").classes("text-red-600 font-semibold")
                return
            spinner_novidade.set_visibility(False)

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

    _EMOJI_CRIT = {'Alta': '🔴', 'Media': '🟡', 'Baixa': '🟢'}
    _META_DIAS  = {'Alta': 7,    'Media': 14,    'Baixa': 35}
    _META_PERC  = 70  # percentual mínimo para meta atingida

    # CTE reutilizada nas duas queries
    _CTE_BASE = """
    WITH ultima_classificacao AS (
        SELECT DISTINCT ON (si.soa_id)
            si.soa_id,
            si.soa_classificacoes_id,
            si.created          AS data_classificacao,
            si.interacao_criada_por AS classificador_id
        FROM soa_interacoes si
        WHERE si.soa_classificacoes_id IS NOT NULL
        ORDER BY si.soa_id, si.created DESC
    ),
    base AS (
        SELECT
            s.sequencial,
            COALESCE(uc.data_classificacao, s.data_classificacao) AS data_classificacao,
            COALESCE(fi.nome, fs.nome)                            AS classificador,
            scr.descricao                                         AS criticidade,
            s.data_conclusao,
            (
                SELECT COUNT(*) - 1
                FROM generate_series(
                    COALESCE(uc.data_classificacao, s.data_classificacao)::date,
                    s.data_conclusao::date,
                    interval '1 day'
                ) AS d
                WHERE EXTRACT(ISODOW FROM d) < 6
            ) AS dias_uteis
        FROM soas s
        LEFT JOIN ultima_classificacao uc  ON uc.soa_id = s.id
        INNER JOIN soa_classificacoes scf
            ON scf.id = COALESCE(uc.soa_classificacoes_id, s.soa_classificacoes_id)
        LEFT JOIN funcionarios fi  ON fi.id = uc.classificador_id
        LEFT JOIN funcionarios fs  ON fs.id = s.funcionario_classificacao_id
        LEFT JOIN soa_criticidades scr ON scr.id = s.soa_criticidade_id
        WHERE scf.descricao = 'Incidente/Erro no Sistema'
          AND COALESCE(uc.data_classificacao, s.data_classificacao) IS NOT NULL
          AND s.data_conclusao IS NOT NULL
          AND s.data_conclusao >= $1
          AND s.data_conclusao <  $2
    )
    """

    _COND_META = """
        (criticidade = 'Alta'  AND dias_uteis <= 7)
     OR (criticidade = 'Media' AND dias_uteis <= 14)
     OR (criticidade = 'Baixa' AND dias_uteis <= 35)
    """

    _QUERY_RESUMO = _CTE_BASE + f"""
    SELECT
        criticidade,
        COUNT(*) AS total,
        COUNT(CASE WHEN {_COND_META} THEN 1 END) AS dentro_meta,
        ROUND(
            100.0 * COUNT(CASE WHEN {_COND_META} THEN 1 END)
            / NULLIF(COUNT(*), 0),
        2) AS perc_meta
    FROM base
    WHERE criticidade IS NOT NULL
    GROUP BY criticidade
    ORDER BY CASE criticidade WHEN 'Alta' THEN 1 WHEN 'Media' THEN 2 WHEN 'Baixa' THEN 3 ELSE 4 END;
    """

    _QUERY_DETALHE = _CTE_BASE + f"""
    SELECT
        sequencial,
        data_classificacao,
        classificador,
        criticidade,
        data_conclusao,
        dias_uteis,
        CASE WHEN {_COND_META} THEN TRUE ELSE FALSE END AS dentro_meta
    FROM base
    ORDER BY sequencial;
    """

    async def calcular_soas_erro(mes: int, ano: int):
        data_inicio = date(ano, mes, 1)
        data_fim    = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)

        conn = await conectar_ao_banco()
        try:
            resumo  = await conn.fetch(_QUERY_RESUMO,  data_inicio, data_fim)
            detalhe = await conn.fetch(_QUERY_DETALHE, data_inicio, data_fim)
        finally:
            await conn.close()
        return {'resumo': resumo, 'detalhe': detalhe}

    ui.label('🔴 Tempo de análise - SOAs de Erro').classes('font-bold text-lg mt-6')
    ui.label('Medição mensal')
    ui.label('Meta: 🔴 Alta ≤ 7 dias úteis | 🟡 Média ≤ 14 dias úteis | 🟢 Baixa ≤ 35 dias úteis')

    with ui.card().classes("p-6 w-full mt-4 shadow-lg rounded-2xl"):
        ui.label("📊 Meta - Tempo de Análise de SOAs de Erro").classes("text-2xl font-bold mb-4 text-center")

        with ui.row().classes("gap-4 items-end flex-wrap"):
            ano1_input = ui.number(label="Ano", value=datetime.now().year,  min=2000, max=2100).classes("w-28")
            mes1_input = ui.number(label="Mês", value=datetime.now().month, min=1,    max=12  ).classes("w-28")

        spinner_erro = ui.spinner('dots', size='lg').classes('mx-auto mt-2')
        spinner_erro.set_visibility(False)
        resultado_erro = ui.column().classes("w-full mt-4")

        async def on_calcular():
            resultado_erro.clear()
            spinner_erro.set_visibility(True)
            try:
                dados = await calcular_soas_erro(int(mes1_input.value), int(ano1_input.value))
            except Exception as e:
                spinner_erro.set_visibility(False)
                with resultado_erro:
                    ui.label(f"❌ Erro ao consultar banco de dados: {e}").classes("text-red-600 font-semibold")
                return
            spinner_erro.set_visibility(False)
            resumo  = dados['resumo']
            detalhe = dados['detalhe']

            if not resumo:
                with resultado_erro:
                    ui.label("Nenhum SOA de Erro encontrado para este período.").classes("text-gray-500 text-center text-lg")
                return

            with resultado_erro:
                # ── Totais gerais ─────────────────────────────────────────
                total_geral      = sum(r['total']       for r in resumo)
                dentro_meta_ger  = sum(r['dentro_meta'] for r in resumo)
                atrasados_geral  = total_geral - dentro_meta_ger
                perc_geral       = round(dentro_meta_ger / total_geral * 100, 1) if total_geral else 0

                with ui.card().classes("w-full p-4 mb-4 bg-gray-50").props("flat bordered"):
                    ui.label("📋 Resumo Geral do Período").classes("font-semibold text-gray-700 mb-2")
                    with ui.row().classes("gap-6 flex-wrap items-center"):
                        with ui.column().classes("items-center"):
                            ui.label(str(total_geral)).classes("text-3xl font-bold text-gray-800")
                            ui.label("Total de SOAs").classes("text-sm text-gray-500")
                        with ui.column().classes("items-center"):
                            ui.label(str(dentro_meta_ger)).classes("text-3xl font-bold text-green-600")
                            ui.label("Dentro do prazo").classes("text-sm text-gray-500")
                        with ui.column().classes("items-center"):
                            ui.label(str(atrasados_geral)).classes("text-3xl font-bold text-red-600")
                            ui.label("Atrasados").classes("text-sm text-gray-500")
                        with ui.column().classes("items-center"):
                            cor_perc = "text-green-600" if perc_geral >= _META_PERC else "text-red-600"
                            ui.label(f"{perc_geral}%").classes(f"text-3xl font-bold {cor_perc}")
                            ui.label(f"Meta: ≥ {_META_PERC}%").classes("text-sm text-gray-500")

                # ── Cards por criticidade ─────────────────────────────────
                ui.label("Resultado por Criticidade").classes("font-semibold text-gray-700 mb-2")
                with ui.row().classes("gap-4 flex-wrap"):
                    for r in resumo:
                        crit   = r['criticidade']
                        emoji  = _EMOJI_CRIT.get(crit, '⚪')
                        meta_d = _META_DIAS.get(crit, '?')
                        perc   = float(r['perc_meta']) if r['perc_meta'] is not None else 0.0
                        ok     = perc >= _META_PERC
                        cor    = 'text-green-600' if ok else 'text-red-600'

                        atrasados_crit = r['total'] - r['dentro_meta']
                        with ui.card().classes("p-4 text-center flex-1").props("flat bordered"):
                            ui.label(f"{emoji} Criticidade {crit}").classes("font-bold text-base")
                            ui.label(f"Prazo: ≤ {meta_d} dias úteis").classes("text-xs text-gray-400 mt-1")
                            ui.label(f"Meta: ≥ {_META_PERC}% no prazo").classes("text-xs text-gray-400")
                            ui.label(f"{r['dentro_meta']} no prazo / {r['total']} total").classes("text-sm text-gray-600 mt-2")
                            ui.label(f"⚠️ {atrasados_crit} atrasado{'s' if atrasados_crit != 1 else ''}").classes(
                                "text-sm text-red-500 font-semibold" if atrasados_crit > 0 else "text-sm text-gray-400"
                            )
                            ui.label(f"{perc:.1f}%").classes(f"text-2xl font-bold {cor} mt-1")
                            ui.label("✅ Meta atingida" if ok else "⚠️ Fora da meta").classes(f"text-sm {cor} mt-1")

                # ── Tabela de detalhamento (colapsável) ──────────────────
                colunas_det = [
                    {'name': 'sequencial',         'label': 'SOA',               'field': 'sequencial',         'align': 'left'  },
                    {'name': 'criticidade',        'label': 'Criticidade',       'field': 'criticidade',        'align': 'left'  },
                    {'name': 'classificador',      'label': 'Classificador',     'field': 'classificador',      'align': 'left'  },
                    {'name': 'data_classificacao', 'label': 'Data Classificação','field': 'data_classificacao', 'align': 'left'  },
                    {'name': 'data_conclusao',     'label': 'Conclusão',         'field': 'data_conclusao',     'align': 'left'  },
                    {'name': 'dias_uteis',         'label': 'Dias Úteis',        'field': 'dias_uteis',         'align': 'center'},
                    {'name': 'status',             'label': 'Status',            'field': 'status',             'align': 'center'},
                ]
                rows_det = [
                    {
                        'sequencial':         r['sequencial'],
                        'criticidade':        r['criticidade'] or 'N/A',
                        'classificador':      r['classificador'] or '-',
                        'data_classificacao': r['data_classificacao'].strftime('%d/%m/%Y') if r['data_classificacao'] else '-',
                        'data_conclusao':     r['data_conclusao'].strftime('%d/%m/%Y')     if r['data_conclusao']     else '-',
                        'dias_uteis':         int(r['dias_uteis']) if r['dias_uteis'] is not None else '-',
                        'status':             '✅' if r['dentro_meta'] else '⚠️',
                    }
                    for r in detalhe
                ]
                with ui.expansion(
                    f'📋 Detalhamento dos SOAs — {len(rows_det)} registros',
                    icon='table_rows',
                ).classes("w-full mt-4 border border-gray-200 rounded-xl"):
                    ui.table(columns=colunas_det, rows=rows_det, row_key='sequencial').classes("w-full")

        ui.button("Calcular", on_click=lambda: asyncio.create_task(on_calcular())).classes("mt-4 bg-blue-600 text-white w-full")