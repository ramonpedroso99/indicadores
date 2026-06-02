import asyncio
from nicegui import ui
from datetime import datetime, date
from conexao import conectar_ao_banco

print(">>> Módulo rh_method carregado!")

cores_botoes = "bg-blue-600 rounded-2xl"

def conteudo_rh():
    async def contar_funcionarios(ano: int, mes: int) -> int:
        inicio_mes = date(ano, mes, 1)
        fim_mes = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)

        query = """
            SELECT COUNT(*) AS total
            FROM funcionarios
            WHERE
                data_admissao < $1
                AND (
                    status_funcionario_id = 1
                    OR data_demissao >= $2
                )
            AND nome NOT IN (
                'Sala de Reuniões 2 - 6º andar',
                'Alura',
                'Sala de Reuniões 1 - 6º andar',
                'Sala de Treinamentos - 4º andar ',
                'Projecti2',
                'Sala de Reuniões - Comercial'
            );
        """
        conn = await conectar_ao_banco()
        total = await conn.fetchval(query, fim_mes, inicio_mes)
        await conn.close()
        return total

    async def buscar_treinamentos(data_inicio: str, data_fim: str):
        query = f"""
            SELECT *
            FROM treinamentos
            LEFT JOIN treinamentos_participantes ON treinamentos_participantes.treinamento_id = treinamentos.id
            LEFT JOIN funcionarios ON funcionarios.id = treinamentos_participantes.participante_id
            LEFT JOIN wc_cursos ON wc_cursos.id = treinamentos.wc_curso_id
            LEFT JOIN wc_curso_status ON wc_curso_status.id = wc_cursos.wc_curso_status_id
            WHERE treinamentos.data BETWEEN '{data_inicio}' AND '{data_fim}'
            AND funcionarios.status_funcionario_id = 1
            AND wc_cursos.wc_curso_status_id = 2
        """
        conn = await conectar_ao_banco()
        rows = await conn.fetch(query)
        await conn.close()
        return rows

    async def somar_carga_horaria(data_inicio: str, data_fim: str) -> float:
        query = f"""
            SELECT
                SUM(
                    (CAST(SPLIT_PART(treinamentos.carga_horaria, ':', 1) AS INTEGER)) + 
                    (CAST(SPLIT_PART(treinamentos.carga_horaria, ':', 2) AS INTEGER)) / 60.0
                ) AS total_horas_treinamento
            FROM treinamentos
            LEFT JOIN treinamentos_participantes ON treinamentos_participantes.treinamento_id = treinamentos.id
            LEFT JOIN funcionarios ON funcionarios.id = treinamentos_participantes.participante_id
            LEFT JOIN wc_cursos ON wc_cursos.id = treinamentos.wc_curso_id
            LEFT JOIN wc_curso_status ON wc_curso_status.id = wc_cursos.wc_curso_status_id
            WHERE treinamentos.data BETWEEN '{data_inicio}' AND '{data_fim}'
            AND funcionarios.status_funcionario_id = 1
            AND wc_cursos.wc_curso_status_id = 2;
        """
        conn = await conectar_ao_banco()
        total = await conn.fetchval(query)
        await conn.close()
        return total or 0

    # Interface com as metas escritas
    ui.label('🔴 Treinamento atual - Horas de treinamento').classes('font-bold text-lg')
    ui.label('Medição anual, últimos 12 meses')
    ui.label('Resultado: Dividir o total de funcionários ativos pela quantidade total de horas de treinamento.')
    # ---------- INTERFACE COM ESTILO ----------
    ui.label('📊 Meta - Horas de Treinamento').classes('text-3xl font-bold text-black-700 mb-6')

    # --- CARD 1: Funcionários Ativos ---
    with ui.card().classes('p-6 mb-6 shadow-lg bg-white rounded-xl'):
        ui.label('👥 Funcionários Ativos no Mês').classes('text-xl font-semibold mb-4')

        with ui.row().classes('gap-4'):
            ano = ui.number('Ano', value=datetime.now().year, format='%.0f', min=2000, max=2100).classes('w-32')
            mes = ui.number('Mês (1-12)', value=datetime.now().month, format='%.0f', min=1, max=12).classes('w-32')
            with ui.card().classes("rounded-2xl"):
                resultado_funcionarios = ui.label('Total de funcionários ativos:').classes('text-md font-semibold mt-2')

        async def consultar_funcionarios():
            resultado_funcionarios.set_text('')
            spinner = ui.spinner(size='lg').classes('mt-2')
            try:
                total = await contar_funcionarios(int(ano.value), int(mes.value))
                resultado_funcionarios.set_text(f'Total de funcionários ativos: {total}')
                ui.notify('Consulta concluída com sucesso!', type='positive')
            except Exception as e:
                resultado_funcionarios.set_text('Erro ao consultar')
                ui.notify(f'Erro: {e}', type='negative')
            spinner.delete()

        ui.button('Consultar Funcionários', on_click=consultar_funcionarios).classes(cores_botoes)

    # --- CARD 2: Treinamentos ---
    with ui.card().classes('p-6 shadow-lg bg-white rounded-xl'):
        ui.label('📚 Treinamentos Realizados').classes('text-xl font-semibold mb-4')

        with ui.row().classes('gap-4'):
            data_inicio = ui.date(value='2024-09-01').classes('mb-2')
            data_fim = ui.date(value='2025-08-30').classes('mb-2')
            with ui.card().classes("rounded-2xl"):
                resultado_carga = ui.label('Total de horas de treinamento: 0.00').classes('mt-2 font-semibold')

        async def consultar_treinamentos():
            resultado_carga.set_text('')
            spinner = ui.spinner(size='lg').classes('mt-2')
            try:
                await buscar_treinamentos(data_inicio.value, data_fim.value)
                total_horas = await somar_carga_horaria(data_inicio.value, data_fim.value)
                resultado_carga.set_text(f'Total de horas de treinamento: {total_horas:.2f}')
                ui.notify('Consulta concluída com sucesso!', type='positive')
            except Exception as e:
                resultado_carga.set_text('Erro ao consultar')
                ui.notify(f'Erro: {e}', type='negative')
            spinner.delete()

        ui.button('Consultar Treinamentos', on_click=consultar_treinamentos).classes(cores_botoes)

    # --- CARD 3: Funcionários com Treinamentos ---
    with ui.card().classes('p-6 mt-6 shadow-lg bg-white rounded-xl'):
        ui.label('👨‍💼 Funcionários com Treinamentos Realizados').classes('text-xl font-semibold mb-4')

        with ui.row().classes('gap-4'):
            ano_treinamento = ui.number('Ano', value=datetime.now().year, format='%.0f', min=2000, max=2100).classes('w-32')
            mes_treinamento = ui.number('Mês (1-12)', value=datetime.now().month, format='%.0f', min=1, max=12).classes('w-32')
            with ui.card().classes("rounded-2xl w-full"):
                tabela_treinamentos = ui.table(
                    columns=[
                        {"name": "nome_funcionario", "label": "Funcionário", "field": "nome_funcionario", "align": "left"},
                        {"name": "nome_treinamento", "label": "Treinamento", "field": "nome_treinamento", "align": "left"},
                        {"name": "data", "label": "Data", "field": "data", "align": "left"},
                        {"name": "carga_horaria", "label": "Carga Horária", "field": "carga_horaria", "align": "left"},
                    ],
                    rows=[],
                ).classes("w-full")

        async def consultar_treinamentos_funcionarios():
            tabela_treinamentos.rows = []
            spinner = ui.spinner(size='lg').classes('mt-2')
            try:
                # Calculando início e fim do mês
                inicio_mes = date(int(ano_treinamento.value), int(mes_treinamento.value), 1)
                fim_mes = date(inicio_mes.year + 1, 1, 1) if inicio_mes.month == 12 else date(inicio_mes.year, inicio_mes.month + 1, 1)

                query = """
                    SELECT
                    funcionarios.nome AS nome_funcionario,
                    treinamentos.treinamento AS nome_treinamento,
                    treinamentos.data,
                    treinamentos.carga_horaria
                    FROM treinamentos
                    LEFT JOIN treinamentos_participantes ON treinamentos_participantes.treinamento_id = treinamentos.id
                    LEFT JOIN funcionarios ON funcionarios.id = treinamentos_participantes.participante_id
                    LEFT JOIN wc_cursos ON wc_cursos.id = treinamentos.wc_curso_id
                    WHERE treinamentos.data BETWEEN $1 AND $2
                    AND funcionarios.status_funcionario_id = 1
                    AND wc_cursos.wc_curso_status_id = 2
                    ORDER BY funcionarios.nome, treinamentos.data;
                """
                conn = await conectar_ao_banco()
                rows = await conn.fetch(query, inicio_mes, fim_mes)
                await conn.close()

                tabela_treinamentos.rows = [
                    {
                        "nome_funcionario": r["nome_funcionario"],
                        "nome_treinamento": r["nome_treinamento"],
                        "data": r["data"].strftime("%Y-%m-%d"),
                        "carga_horaria": r["carga_horaria"]
                    }
                    for r in rows
                ]
                ui.notify(f'{len(rows)} registros encontrados', type='positive')

            except Exception as e:
                ui.notify(f'Erro: {e}', type='negative')
            spinner.delete()

        ui.button("Consultar", on_click=consultar_treinamentos_funcionarios).classes(cores_botoes)

    with ui.card().classes("p-6 mt-6 shadow-lg bg-white rounded-xl"):
        ui.label("🔎 Pesquisa de Treinamentos Por Funcionário").classes("text-xl font-semibold mb-4")

        tipo_busca = ui.select(
            options=["Colaborador"],
            value="Colaborador",
            label="Buscar por"
        ).classes("mb-2 font-bold")

        input_colaborador = ui.input(placeholder="Digite o nome do colaborador...").classes("mb-2 font-bold")
        lista_sugestoes = ui.column().style("max-height: 200px; overflow-y: auto;").classes(
            "border rounded-lg p-2 bg-white"
        ).style("display: none;")

        dropdown_setores = ui.select(options=[]).classes("mb-2 font-bold").style("display: none;")

        
        tabela_resultados = ui.table(
            columns=[
                {"name": "nome_treinamento", "label": "Treinamento", "field": "nome_treinamento", "align": "left"},
                {"name": "data", "label": "Data", "field": "data", "align": "left"},
                {"name": "carga_horaria", "label": "Carga Horária", "field": "carga_horaria", "align": "left"},
            ],
            rows=[],
        ).classes("w-full mt-4")

        
        # Carrega setores disponíveis no select
        async def carregar_setores():
            conn = await conectar_ao_banco()
            setores = await conn.fetch("SELECT DISTINCT descricao FROM setores ORDER BY descricao;")
            await conn.close()
            dropdown_setores.options = [s["descricao"] for s in setores]

        asyncio.create_task(carregar_setores())

        # 🔹 Busca nomes de colaboradores conforme digitação
        async def buscar_colaboradores_parcial(texto: str):
            if not texto or len(texto.strip()) < 2:
                lista_sugestoes.style("display: none;")
                return

            conn = await conectar_ao_banco()
            query = """
                SELECT nome 
                FROM funcionarios 
                WHERE nome ILIKE $1 
                AND status_funcionario_id = 1
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

        # Atualiza lista conforme o usuário digita
        input_colaborador.on(
            "update:model-value",
            lambda e: asyncio.create_task(buscar_colaboradores_parcial(e.args))
        )

        container_spinner = ui.row().classes("justify-center mt-2")
        spinner = ui.spinner(size="lg").classes("hidden")  # começa invisível
        with container_spinner:
            spinner

        # 🔍 Função principal para buscar treinamentos
        async def buscar():
            tabela_resultados.rows = []
            termo = input_colaborador.value.strip()

            if not termo:
                ui.notify("Digite ou selecione um valor para buscar.", type="warning")
                return

            spinner.classes(remove="hidden")

            try:
                if tipo_busca.value == "Colaborador":
                    query = """
                        SELECT
                            f.nome AS nome_funcionario,
                            t.treinamento AS nome_treinamento,
                            t.data,
                            t.carga_horaria
                        FROM treinamentos t
                        LEFT JOIN treinamentos_participantes tp ON tp.treinamento_id = t.id
                        LEFT JOIN funcionarios f ON f.id = tp.participante_id
                        LEFT JOIN wc_cursos wc ON wc.id = t.wc_curso_id
                        WHERE f.nome = $1
                        AND f.status_funcionario_id = 1
                        AND wc.wc_curso_status_id = 2
                        ORDER BY t.data DESC;
                    """
                    params = (termo,)
                else:
                    query = """
                        SELECT
                            f.nome AS nome_funcionario,
                            t.treinamento AS nome_treinamento,
                            t.data,
                            t.carga_horaria
                        FROM treinamentos t
                        LEFT JOIN treinamentos_participantes tp ON tp.treinamento_id = t.id
                        LEFT JOIN funcionarios f ON f.id = tp.participante_id
                        LEFT JOIN setores s ON s.id = f.setor_id
                        LEFT JOIN wc_cursos wc ON wc.id = t.wc_curso_id
                        WHERE s.descricao = $1
                        AND f.status_funcionario_id = 1
                        AND wc.wc_curso_status_id = 2
                        ORDER BY f.nome, t.data DESC;
                    """
                    params = (termo,)

                conn = await conectar_ao_banco()
                rows = await conn.fetch(query, *params)
                await conn.close()

                tabela_resultados.rows = [
                    {
                        "nome_treinamento": r["nome_treinamento"],
                        "data": r["data"].strftime("%Y-%m-%d"),
                        "carga_horaria": r["carga_horaria"],
                    }
                    for r in rows
                ]

                if rows:
                    ui.notify(f"{len(rows)} treinamentos encontrados.", type="positive")
                else:
                    ui.notify("Nenhum treinamento encontrado.", type="info")

            except Exception as e:
                ui.notify(f"Erro: {e}", type="negative")
            
            finally:
                spinner.classes(add="hidden")
            
            
        ui.button("Consultar", on_click=buscar).classes(cores_botoes)
