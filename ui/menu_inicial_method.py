from nicegui import ui
import asyncio
import asyncpg
from datetime import datetime

print(">>> Módulo menu_inicial_method carregado!")

ARQUIVO_METAS = "documentos/metas.pdf"

COLUNAS_RESUMO = [
    {'name': 'name',  'label': '🏢 Setor',      'field': 'name',  'align': 'left'},
    {'name': 'indi',  'label': '📝 Indicador',   'field': 'indi',  'align': 'left'},
    {'name': 'MetaA', 'label': '📊 Meta Geral',  'field': 'MetaA', 'align': 'left'},
]

RESUMO_METAS = [
    {'name': '🧑‍🤝‍🧑 Gente e Gestão',      'indi': 'Treinamentos realizados',       'MetaA': 'Média de 45hrs por colaborador em 12 meses'},
    {'name': '🧑‍🤝‍🧑 Gente e Gestão',      'indi': 'Avaliação de Competência',      'MetaA': 'Organizar o número de respostas e pendências'},
    {'name': '💼 Comercial',               'indi': 'Taxa de Conversão Comercial',   'MetaA': '15% ao mês para Prospectos'},
    {'name': '🌐 Operações',               'indi': 'Pesquisa de Satisfação Viagem', 'MetaA': 'Obter 80% das avaliações positivas'},
    {'name': '🗣️ Atendimento ao Cliente', 'indi': 'Pesquisa SOA',                  'MetaA': 'Obter 80% das avaliações positivas nos SOAs'},
    {'name': '🗣️ Atendimento ao Cliente', 'indi': 'Meta de Atendimento de SOA',    'MetaA': '80% atendidos em até 5 horas'},
    {'name': '🖥️ Desenvolvimento',        'indi': 'SOAs Novidade',                 'MetaA': '80% dos SOAs atendidos em até 15 dias úteis e 100% em 30 dias úteis'},
    {'name': '🖥️ Desenvolvimento',        'indi': 'SOAs Erro',                     'MetaA': '70% dos SOAs em 72 horas úteis e 100% em 13 dias úteis'},
]

COLUNAS_RESULTADO = [
    {'name': 'setor',      'label': '🏢 Setor',      'field': 'setor',      'align': 'left'},
    {'name': 'indicador',  'label': '📈 Indicador',   'field': 'indicador',  'align': 'left'},
    {'name': 'meta_geral', 'label': '🎯 Meta Geral',  'field': 'meta_geral', 'align': 'left'},
    {'name': 'resultado',  'label': '🔎 Resultado',   'field': 'resultado',  'align': 'left'},
]


async def _get_connection():
    return await asyncpg.connect(
        user='postgres',
        password='1205',
        database='indicadores_wareline',
        host='localhost',
        port='5433',
    )


def conteudo_menu_inicial():
    # ── Documento de metas ────────────────────────────────────────────────
    ui.label("📁 Documento — Metas").classes("font-bold text-lg text-gray-700 mb-2")

    with ui.card().classes("rounded-xl w-full mb-5 p-4"):
        ui.label("Para acessar o setor desejado, clique na barra lateral à esquerda.").classes("text-gray-600")
        ui.label("Clique abaixo para baixar o documento oficial das metas a serem atingidas.").classes("text-gray-600 mt-1")
        ui.button(
            "📥 Baixar Documento",
            on_click=lambda: ui.download(ARQUIVO_METAS)
        ).props("color=positive").classes("mt-3")

    # ── Resumo estático dos indicadores ──────────────────────────────────
    ui.label("🔍 Indicadores — Overview").classes("font-bold text-lg text-gray-700 mb-2")

    with ui.card().classes("rounded-xl w-full mb-5 p-4"):
        ui.label("📊 Resumo dos indicadores por setor").classes("font-semibold text-base text-gray-700 mb-3")
        ui.table(
            columns=COLUNAS_RESUMO,
            rows=RESUMO_METAS,
            row_key='indi',
        ).classes("rounded-xl w-full")

    # ── Indicadores por período (banco local) ─────────────────────────────
    ui.label("📅 Indicadores por Período").classes("font-bold text-lg text-gray-700 mb-2")

    resultado = ui.column().classes("w-full mt-2")

    async def buscar():
        resultado.clear()
        try:
            conn = await _get_connection()
            rows = await conn.fetch(
                "SELECT setor, indicador, meta_geral, resultado FROM indicadores WHERE ano=$1 AND mes=$2",
                int(ano.value), int(mes.value),
            )
            await conn.close()
            dados = [dict(r) for r in rows]
        except Exception as e:
            with resultado:
                ui.notify(f"Erro ao buscar dados: {e}", type='negative')
            return

        with resultado:
            if dados:
                ui.label(
                    f"📅 Indicadores de {int(mes.value):02d}/{int(ano.value)}"
                ).classes("font-semibold text-gray-700 mb-2")
                ui.table(
                    columns=COLUNAS_RESULTADO,
                    rows=dados,
                    row_key='indicador',
                ).classes("rounded-xl w-full")
            else:
                ui.label(
                    f"Sem dados para {int(mes.value):02d}/{int(ano.value)}"
                ).classes("text-red-500 font-semibold")

    with ui.card().classes("rounded-xl w-full p-4"):
        ui.label("Filtrar por período").classes("font-semibold text-gray-700 mb-3")
        with ui.row().classes("gap-4 items-end flex-wrap"):
            ano = ui.number('Ano', value=datetime.now().year, format='%d', min=2000, max=2100).classes('w-28')
            mes = ui.number('Mês (1-12)', value=datetime.now().month, format='%d', min=1, max=12).classes('w-28')
            ui.button(
                "🔍 Buscar",
                on_click=lambda: asyncio.create_task(buscar())
            ).props("color=positive")
