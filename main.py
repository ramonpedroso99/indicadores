from nicegui import ui
from backend.rh_method import conteudo_rh
from backend.comercial_method import conteudo_comercial
from backend.operacoes_method import conteudo_operacoes
from backend.atendimento_cliente_method import conteudo_atendimento_cliente
from backend.metas_method import conteudo_metas
from backend.desenvolvimento_method import conteudo_desenvolvimento
from ui.menu_inicial_method import conteudo_menu_inicial
from backend.ava_competencia_method import conteudo_ava_competencia
from datetime import datetime
import sys
import os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path

NAVEGACAO = [
    ('🏠 Menu Inicial', '/'),
    ('🧑‍🤝‍🧑 Gente e Gestão', '/rh'),
    ('💼 Comercial', '/comercial'),
    ('🌐 Operações', '/operacoes'),
    ('🗣️ Atendimento ao Cliente', '/atendimento'),
    ('🎯 Metas', '/metas'),
    ('🖥️ Desenvolvimento', '/desenvolvimento'),
    ('📝 Avaliação de Competência', '/ava_competencia'),
]

def layout_com_menu(titulo: str, conteudo_func, rota_atual: str = '/'):
    ui.add_head_html('''
    <style>
      body { background: #f1f5f9; margin: 0; }
      .q-btn { text-transform: none !important; letter-spacing: normal !important; }
      .nav-btn .q-btn__content { justify-content: flex-start; }
    </style>
    ''')

    aberta = {'v': True}

    with ui.row().classes('w-full min-h-screen items-stretch').style('gap: 0;'):

        # ── Sidebar ──────────────────────────────────────────────────────
        with ui.column().classes(
            'bg-gradient-to-b from-red-800 to-blue-600 text-white shadow-xl'
        ).style('width: 230px; min-width: 230px; flex-shrink: 0; padding: 1rem 0; gap: 0;') as sidebar:

            with ui.row().classes('px-4 pb-3 items-center justify-between w-full'):
                ui.label('Indicadores').classes('text-base font-bold tracking-wide')
                ui.button('✕', on_click=lambda: toggle()).classes('text-white').props('flat dense round')

            ui.image(resource_path('./images/logo.png')).classes('px-4 mb-4 rounded-xl')

            for label, rota in NAVEGACAO:
                ativo = rota == rota_atual
                ui.button(
                    label,
                    on_click=lambda r=rota: ui.navigate.to(r)
                ).classes(
                    'w-full text-left text-white text-sm nav-btn ' +
                    ('bg-white/30 font-semibold' if ativo else 'hover:bg-white/15')
                ).props('flat align=left')

        # ── Conteúdo principal ────────────────────────────────────────────
        with ui.column().classes('flex-1 p-6').style('background: #f1f5f9; min-width: 0; gap: 0;'):

            with ui.row().classes('items-center mb-5 gap-3'):
                ui.button('☰', on_click=lambda: toggle()).classes(
                    'bg-red-800 text-white rounded-lg shadow-sm'
                ).props('dense')
                ui.label(titulo).classes('text-2xl font-bold text-gray-800')

            with ui.card().classes('w-full p-6 bg-white shadow-sm rounded-xl border border-gray-100'):
                conteudo_func()

            ui.image(resource_path('./images/sub_fachada.png')).classes('w-full mt-6 rounded-xl opacity-90')

    def toggle():
        aberta['v'] = not aberta['v']
        sidebar.set_visibility(aberta['v'])


# ── Páginas ──────────────────────────────────────────────────────────────────

@ui.page('/')
def home():
    layout_com_menu("🏠 Menu Inicial", conteudo_menu_inicial, '/')

@ui.page('/rh')
def rh():
    layout_com_menu("🧑‍🤝‍🧑 Gente e Gestão", conteudo_rh, '/rh')

@ui.page('/comercial')
def comercial():
    layout_com_menu("💼 Comercial", conteudo_comercial, '/comercial')

@ui.page('/operacoes')
def operacoes():
    layout_com_menu("🌐 Operações", conteudo_operacoes, '/operacoes')

@ui.page('/atendimento')
def atendimento_cliente():
    layout_com_menu("🗣️ Atendimento ao Cliente", conteudo_atendimento_cliente, '/atendimento')

@ui.page('/metas')
def metas():
    layout_com_menu("🎯 Metas", conteudo_metas, '/metas')

@ui.page('/desenvolvimento')
def desenvolvimento():
    layout_com_menu("🖥️ Desenvolvimento", conteudo_desenvolvimento, '/desenvolvimento')

@ui.page('/ava_competencia')
def ava_competencia():
    layout_com_menu("📝 Avaliação de Competência", conteudo_ava_competencia, '/ava_competencia')


data_hoje = datetime.today()
print(">>> Iniciando app...")
print(f">>> Rodando em: {data_hoje}")

ui.run(
    title="Indicadores - Wareline",
    reload=False,
    favicon=resource_path('images/icone_indicadores.ico'),
    host='0.0.0.0',
    port=20000,
)
