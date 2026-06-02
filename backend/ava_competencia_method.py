import asyncio
import asyncpg
from nicegui import ui
from datetime import datetime
from conexao import conectar_ao_banco

def conteudo_ava_competencia():
    async def buscar_avaliacoes(so_pendentes=False):
        conn = await conectar_ao_banco()

        query = """
            SELECT 
            aa.id AS avaliacao_id,
            f.nome AS colaborador,
            s.descricao AS setor_descricao,
            aa.created AS dia_criacao,
            aa.data_conclusao AS dia_conclusao,
            CASE 
                WHEN aa.data_conclusao IS NOT NULL THEN 'Concluída'
                ELSE 'Não Concluída'
            END AS situacao,
            CASE 
            WHEN aa.data_conclusao IS NULL THEN 
            GREATEST(DATE_PART('day', NOW() - aa.created) - 90, 0)
            ELSE 
            GREATEST(DATE_PART('day', aa.data_conclusao - aa.created) - 90, 0)
        END AS dias_atraso
        FROM auto_avaliacoes aa
        LEFT JOIN funcionarios f ON f.id = aa.funcionario_id
        LEFT JOIN setores s ON s.id = f.setor_id
        WHERE aa.created BETWEEN '2010-01-01' AND '2030-01-01'
        AND f.id NOT IN (418,210,212,486)
        AND f.status_funcionario_id = '1'
        ORDER BY aa.created ASC;
        """

        if so_pendentes:
            query += " AND aa.data_conclusao IS NULL"

        resultados = await conn.fetch(query)
        await conn.close()

        return [dict(r) for r in resultados]

    # Função para garantir que os valores sejam JSON serializáveis
    def safe_value(value):
        if isinstance(value, set):
            return list(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        elif value is None:
            return "-"
        return value

    # Função para mostrar a tabela com cores
    def mostrar_tabela(avaliacoes):
        if not avaliacoes:
            ui.label("Nenhuma avaliação encontrada.").classes("text-red-600")
            return

        # Prepara os dados da tabela
        colaboradores = []
        for a in avaliacoes:
            row = {
                "ID": safe_value(a['avaliacao_id']),
                "Colaborador": safe_value(a['colaborador']),
                "Criada": safe_value(a['dia_criacao']),
                "Conclusao": safe_value(a['dia_conclusao']),
                "Situacao": safe_value(a['situacao']),
                "Atraso": safe_value(int(a['dias_atraso']))
            }
            colaboradores.append(row)

        ui.table(
            columns=[
                {"name": "ID", "label": "ID", "field": "ID"},
                {"name": "Colaborador", "label": "Colaborador", "field": "Colaborador"},
                {"name": "Criada", "label": "Criada", "field": "Criada"},
                {"name": "Conclusao", "label": "Conclusão", "field": "Conclusao"},
                {"name": "Situacao", "label": "Situação", "field": "Situacao"},
                {"name": "Atraso", "label": "Dias de Atraso", "field": "Atraso"},
            ],
            rows=colaboradores,
            row_key="ID",
        ).classes("w-[900px] rounded-2xl font-semibold")

    ui.label('🔴 Avaliação de Competência - Conclusões e Pendências').classes('font-bold text-lg')
    ui.label('Medição anual, últimos 12 meses')
    ui.label('Resultado: Organizar o número de concluídos e pendentes por colaborador e o número de dias atrasados.')


    with ui.card().classes("rounded-2xl p-6 w-[950px] mt-6"):
        ui.label("📊 Meta - Avaliação de Competência").classes("text-2xl font-bold mb-4")

        selecao = ui.select(
            options=["Todas", "Pendentes"], 
            value="Todas", 
            label="Escolha o tipo de avaliação"
        ).classes("font-bold")
        botao = ui.button("Buscar Avaliações").classes("mt-2").props("color=positive")
        resultado_div = ui.column().classes("mt-4")

        async def ao_clicar():
            resultado_div.clear()
            so_pendentes = selecao.value == "Pendentes"

            todas = await buscar_avaliacoes(False)
            avaliacoes = todas if not so_pendentes else [a for a in todas if a['dia_conclusao'] is None]

            total_avaliacoes = len(todas)
            total_pendentes = sum(1 for a in todas if a['dia_conclusao'] is None)
            total_concluidas = total_avaliacoes - total_pendentes

            perc_concluidas = (total_concluidas / total_avaliacoes * 100) if total_avaliacoes > 0 else 0
            perc_pendentes = (total_pendentes / total_avaliacoes * 100) if total_avaliacoes > 0 else 0

            with resultado_div:
                ui.label(f"📌 Total de Avaliações: {total_avaliacoes}").classes("text-blue-600 font-bold")
                ui.label(f"✅ Concluídas: {total_concluidas} ({perc_concluidas:.1f}%)").classes("text-green-600 font-bold")
                ui.label(f"⏳ Pendentes: {total_pendentes} ({perc_pendentes:.1f}%)").classes("text-red-600 font-bold mb-4")
                
                mostrar_tabela(avaliacoes)
                
        botao.on("click", ao_clicar)

    with ui.card().classes("rounded-2xl p-4 w-[950px] mt-6"):
        ui.label("🔎 Buscar avaliações").classes("font-bold mb-2 text-lg")

        tipo_busca = ui.select(
            options=["Colaborador", "Setor"],
            value="Colaborador",
            label="Buscar por"
        ).classes("mb-2 font-bold")

        # Campo de input com autocomplete
        input_colaborador = ui.input(placeholder="Digite o nome do colaborador...").classes("mb-2 font-bold")
        lista_sugestoes = ui.column().style("max-height: 200px; overflow-y: auto;").classes("border rounded-lg p-2 bg-white").style("display: none;")

        dropdown_setores = ui.select(options=[]).classes("mb-2 font-bold").style("display: none;")

        botao_buscar = ui.button("Buscar").props("color=positive")
        resultado_div_colab = ui.column().classes("mt-4")

        def atualizar_visibilidade():
            if tipo_busca.value == "Colaborador":
                input_colaborador.style("display: block;")
                lista_sugestoes.style("display: block;")
                dropdown_setores.style("display: none;")
            else:
                input_colaborador.style("display: none;")
                lista_sugestoes.style("display: none;")
                dropdown_setores.style("display: block;")

        tipo_busca.on("update:model-value", atualizar_visibilidade)

        async def carregar_setores():
            conn = await asyncpg.connect(user='ramonpedroso', password='9JnJp&ph7c&bf%b9D*2', database='erpv2', host='184.72.149.92')
            setores = await conn.fetch("SELECT DISTINCT descricao FROM setores ORDER BY descricao")
            await conn.close()
            dropdown_setores.options = [s["descricao"] for s in setores]

        asyncio.create_task(carregar_setores())

        # 🔹 Função para buscar sugestões no banco conforme digitação
        async def buscar_colaboradores_parcial(texto: str):
            if not texto or len(texto.strip()) < 2:
                lista_sugestoes.style("display: none;")
                return

            conn = await asyncpg.connect(user='ramonpedroso', password='9JnJp&ph7c&bf%b9D*2', database='erpv2', host='184.72.149.92')
            query = """
                SELECT nome 
                FROM funcionarios 
                WHERE nome ILIKE $1 
                AND status_funcionario_id = '1'
                AND id NOT IN (418,210,212,486)
                ORDER BY nome 
                LIMIT 10;
            """
            resultados = await conn.fetch(query, f"%{texto}%")
            await conn.close()

            lista_sugestoes.clear()
            if resultados:
                lista_sugestoes.style("display: block;")
                for r in resultados:
                    nome = r["nome"]
                    with lista_sugestoes:
                        ui.label(nome).classes("hover:bg-gray-200 p-1 cursor-pointer rounded").on(
                            "click",
                            lambda e, nome=nome: (
                                setattr(input_colaborador, "value", nome),
                                lista_sugestoes.style("display: none;")
                            )
                        )
            else:
                lista_sugestoes.style("display: none;")

        # Escuta evento de digitação no input
        input_colaborador.on("update:model-value", lambda e: asyncio.create_task(buscar_colaboradores_parcial(e.args)))

        async def buscar():
            resultado_div_colab.clear()
            termo = input_colaborador.value.strip() if tipo_busca.value == "Colaborador" else dropdown_setores.value
            if not termo:
                return

            avaliacoes = await buscar_avaliacoes(so_pendentes=False)
            if tipo_busca.value == "Colaborador":
                avaliacoes = [a for a in avaliacoes if a.get("colaborador") and termo.lower() in a["colaborador"].lower()]
            else:
                avaliacoes = [a for a in avaliacoes if a.get("setor_descricao") and termo.lower() in a["setor_descricao"].lower()]

            with resultado_div_colab:
                mostrar_tabela(avaliacoes)

        botao_buscar.on("click", buscar)

    with ui.card().classes("rounded-2xl p-4 w-[950px] mt-6"):
        ui.label("📅 Consultar Avaliações por Mês e Ano").classes("font-bold mb-2 text-lg")

        meses_dict = {
            "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
            "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
            "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
        }

        select_mes = ui.select(options=list(meses_dict.keys()), label="Escolha o mês").classes("font-bold")
        input_ano = ui.input(label="Digite o ano", placeholder="Ex: 2025").classes("font-bold")
        botao_buscar_mes_ano = ui.button("Buscar").props("color=positive").classes("mt-2")
        resultado_div_mes_ano = ui.column().classes("mt-4")

        # Função para garantir que os valores sejam JSON serializáveis
        def safe_value(value):
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d")
            elif value is None:
                return "-"
            return value

        async def buscar_por_mes_ano():
            resultado_div_mes_ano.clear()
            try:
                mes_selecionado = meses_dict.get(select_mes.value)
                ano_digitado = int(input_ano.value.strip())
                if mes_selecionado is None or ano_digitado < 1900:
                    raise ValueError
            except Exception:
                ui.label("❌ Mês ou ano inválido").classes("text-red-600")
                return

            conn = await asyncpg.connect(
                user='ramonpedroso',
                password='9JnJp&ph7c&bf%b9D*2',
                database='erpv2',
                host='184.72.149.92'
            )

            query = """
                SELECT 
                    aa.id AS avaliacao_id,
                    f.nome AS colaborador,
                    aa.created AS dia_criacao,
                    aa.data_conclusao AS dia_conclusao,
                    CASE 
                        WHEN aa.data_conclusao IS NOT NULL THEN 'Concluída'
                        ELSE 'Não Concluída'
                    END AS situacao,
                    CASE 
                    WHEN aa.data_conclusao IS NULL THEN 
                    GREATEST(DATE_PART('day', NOW() - aa.created) - 90, 0)
                    ELSE 
                    GREATEST(DATE_PART('day', aa.data_conclusao - aa.created) - 90, 0)
                END AS dias_atraso
                FROM auto_avaliacoes aa
                LEFT JOIN funcionarios f ON f.id = aa.funcionario_id
                WHERE EXTRACT(MONTH FROM aa.created) = $1
                AND EXTRACT(YEAR FROM aa.created) = $2
                AND f.id NOT IN (418,210,212,486)
                AND f.status_funcionario_id = '1'
                ORDER BY aa.created ASC;
            """
            resultados = await conn.fetch(query, mes_selecionado, ano_digitado)
            await conn.close()

            if not resultados:
                ui.label(f"Nenhuma avaliação encontrada em {select_mes.value} de {ano_digitado}.").classes("text-red-600")
                return
            
            total_avaliacoes = len(resultados)
            total_concluidas = sum(1 for r in resultados if r["dia_conclusao"] is not None)
            total_pendentes = total_avaliacoes - total_concluidas

            perc_concluidas = (total_concluidas / total_avaliacoes * 100) if total_avaliacoes > 0 else 0
            perc_pendentes = (total_pendentes / total_avaliacoes * 100) if total_avaliacoes > 0 else 0

            # Mostrar resumo acima da tabela
            

            # Preparar dados para a tabela
            rows = []
            for r in resultados:
                rows.append({
                    "ID": safe_value(r["avaliacao_id"]),
                    "Colaborador": safe_value(r["colaborador"]),
                    "Criada": safe_value(r["dia_criacao"]),
                    "Conclusao": safe_value(r["dia_conclusao"]),
                    "Situacao": safe_value(r["situacao"]),
                    "Atraso": int(r["dias_atraso"])
                })

            with resultado_div_mes_ano:
                ui.label(f"📌 Total de Avaliações em {select_mes.value}/{ano_digitado}: {total_avaliacoes}").classes("text-blue-600 font-bold")
                ui.label(f"✅ Concluídas: {total_concluidas} ({perc_concluidas:.1f}%)").classes("text-green-600 font-bold")
                ui.label(f"⏳ Pendentes: {total_pendentes} ({perc_pendentes:.1f}%)").classes("text-red-600 font-bold mb-4")
                ui.table(
                    columns=[
                        {"name": "ID", "label": "ID", "field": "ID"},
                        {"name": "Colaborador", "label": "Colaborador", "field": "Colaborador"},
                        {"name": "Criada", "label": "Criada", "field": "Criada"},
                        {"name": "Conclusao", "label": "Conclusão", "field": "Conclusao"},
                        {"name": "Situacao", "label": "Situação", "field": "Situacao"},
                        {"name": "Atraso", "label": "Dias de Atraso", "field": "Atraso"},
                    ],
                    rows=rows,
                    row_key="ID"
                ).classes("w-[900px] rounded-2xl font-semibold")
    
    botao_buscar_mes_ano.on("click", buscar_por_mes_ano)
