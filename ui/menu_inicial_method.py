from nicegui import ui
import asyncio
import asyncpg
from datetime import datetime, date
import asyncio

print(">>> Módulo menu_inicial_method carregado!")

arquivo = "documentos/metas.pdf"

###################### Interface do menu inicial ########################################

def conteudo_menu_inicial():
    ui.label("📁 Documento - Metas").classes("font-bold text-lg")

    with ui.card().classes("rounded-2xl"):
        ui.label("Para acessar o setor desejado, clique na barra lateral à esquerda!").classes("font-bold text-lg")
        ui.label("Clique abaixo no botão para poder baixar o documento oficial das metas a serem atingidas")
        ui.button("Baixar Documento", on_click=lambda: ui.download(arquivo)).props("color=positive").classes("mx-auto")

#------ Interface de avaliação de competência --------#
    ui.label("🔍 Indicadores - Overview").classes("font-bold text-lg")
    
    with ui.card().classes("rounded-2xl w-[900px]"):
        ui.label("📊 Meta - Resumo dos indicadores").classes("font-bold text-lg")
        ui.label("📈 Setores e suas metas").classes("font-bold mx-auto text-lg")
        columns = [
            {'name': 'name', 'label': '🏢 Setor', 'field': 'name', 'required': False, 'align': 'left'},
            {'name': 'indi', 'label': '📝 Indicador', 'field': 'indi', 'sortable': False, 'align': 'left'},
            {'name': 'MetaA', 'label': '📊 Meta Geral', 'field': 'MetaA', 'sortable': False, 'align': 'left'},
            
        ]
        rows = [
            {'name': '🧑‍🤝‍🧑 Gente e Gestão', 'indi': 'Treinamentos realizados', 'MetaA': "Média de 45hrs por colaborador em 12 meses"},
            {'name': '🧑‍🤝‍🧑 Gente e Gestão', 'indi' : 'Avaliação de Compentência', 'MetaA': 'Organizar o número de respostas e pendências'},
            {'name': '💼 Comercial', 'indi': 'Taxa de Conversão Comercial', 'MetaA': '15% ao mês para Prospectos'},
            {'name': '🌐 Operações', 'indi': 'Pesquisa de Satisfação Viagem','MetaA': "Obter 80% das avaliações positivas SOAs"},
            {'name': '🗣️ Atendimento ao cliente', 'indi': 'Pesquisa SOA','MetaA': "Obter 80% das avaliações positivas nos SOAs"},
            {'name': '🗣️ Atendimento ao Cliente', 'indi': 'Meta de Atendimento de SOA','MetaA': "80% atendidos em até 5 horas"},
            {'name': '🖥️ Desenvolvimento', 'indi': 'SOAs Novidade','MetaA': "80% dos SOAs atendidos em até 15 dias úteis e 100% em 30 dias úteis"},
            {'name': '🖥️ Desenvolvimento', 'indi': 'SOAs Erro','MetaA': "70% dos SOAs em 72 horas úteis e 100% em 13 dias úteis"},
        ]
        
        data_hoje = datetime.today()
        data_hoje = data_hoje.replace(microsecond=0)
        with ui.row():
            tabela = ui.table(columns=columns, rows=rows, row_key='name').classes("rounded-2xl mx-auto font-bold")
            #ui.label(f"📅 Data de visualização: {data_hoje}").classes("font-bold mx-auto")
            #ui.label(f"📅 Data de atualização: 11-09-2025").classes("font-bold mx-auto")
    
    

    # --- Conexão com o PostgreSQL ---
    async def get_connection():
        return await asyncpg.connect(
            user='postgres',
            password='1205',
            database='indicadores_wareline',
            host='localhost',
            port='5433'
        )

    # --- Definição das colunas da tabela ---
    columns = [
        {'name': 'setor', 'label': '🏢 Setor', 'field': 'setor', 'align' : 'left'},
        {'name': 'indicador', 'label': '📈 Indicador', 'field': 'indicador', 'align' : 'left'},
        {'name': 'meta_geral', 'label': '🎯 Meta Geral', 'field': 'meta_geral', 'align' : 'left'},
        {'name': 'resultado', 'label': '🔎 Resultado', 'field': 'resultado', 'align' : 'left'},
    ]

    # --- Container que será atualizado a cada busca ---
    resultado = ui.column().classes("mx-auto")

    # --- Função para buscar os dados no banco ---
    async def buscar_dados_do_app(ano: int, mes: int):
        conn = await get_connection()
        rows = await conn.fetch(
            """
            SELECT setor, indicador, meta_geral, resultado
            FROM indicadores
            WHERE ano=$1 AND mes=$2
            """,
            ano, mes
        )
        await conn.close()
        # transforma em lista de dicionários para o NiceGUI
        return [
            {
                'setor': r['setor'],
                'indicador': r['indicador'],
                'meta_geral': r['meta_geral'],
                'resultado': r['resultado']
            }
            for r in rows
        ]

    # --- Interface ---
    with ui.card().classes("rounded-2xl"):
        ui.label("Período das metas").classes("font-bold rounded-2xl")
        
        # número para o ano
        ano = ui.number(
            'Ano', value=datetime.now().year, format='%d', min=2000, max=2100
        ).classes('w-32')
        
        # número para o mês
        mes = ui.number(
            'Mês (1-12)', value=datetime.now().month, format='%d', min=1, max=12
        ).classes('w-32')
        
        # botão que chama a função assíncrona
        ui.button(
            "Buscar",
            on_click=lambda: asyncio.create_task(buscar_teste())
        ).classes("mx-auto").props("color=positive")


    # --- Função chamada ao clicar no botão ---
    async def buscar_teste():
        resultado.clear()  # limpa resultados anteriores
        dados = await buscar_dados_do_app(ano.value, mes.value)
        
        with resultado:
            if dados:
                ui.label(f"📅 Indicadores de {mes.value:.0f}/{ano.value}").classes("font-bold mx-auto")
                ui.table(columns=columns, rows=dados, row_key='indicador').classes("rounded-2xl font-bold")
            else:
                ui.label(f"Sem dados para {mes.value:.0f}/{ano.value}").classes("text-red-500 font-bold mx-auto")



