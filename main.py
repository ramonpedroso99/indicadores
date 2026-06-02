from nicegui import ui
from backend.rh_method import conteudo_rh
from backend.comercial_method import conteudo_comercial
from backend.operacoes_method import conteudo_operacoes
from backend.atendimento_cliente_method import conteudo_atendimento_cliente
from backend.metas_method import conteudo_metas
from backend.desenvolvimento_method import conteudo_desenvolvimento
from ui.menu_inicial_method import conteudo_menu_inicial
from backend.ava_competencia_method import conteudo_ava_competencia
from datetime import date, datetime
import sys
import os

def layout_com_menu(titulo: str, conteudo_func):
    ui.add_head_html('''
    <style>
    body {
        background: linear-gradient(to bottom, #991b1b, #3b82f6); /* red-800 para blue-500 */
    }
    </style>
    ''')
    
    ui.image('./images/fachada1.png')
    
    sidebar_visible = True  # estado da sidebar

    with ui.row().classes('w-full min-h-screen bg-gray-100 relative'):
        # Sidebar
        with ui.column().classes(
            'w-1/6 bg-gradient-to-b from-red-800 to-blue-500 text-white p-6 shadow-xl transition-transform duration-300 relative'
        ) as sidebar:
            ui.label('Setores').classes('text-2xl font-bold mb-6')
            ui.image('./images/logo.png').classes('mx-auto mb-4 rounded-2xl')
            botoes = [
                ('🏠 Menu Inicial', '/'),
                ('🧑‍🤝‍🧑 Gente e Gestão', '/rh'),
                ('💼 Comercial', '/comercial'),
                ('🌐 Operações', '/operacoes'),
                ('🗣️ Atendimento ao Cliente', '/atendimento'),
                ('🎯 Metas', '/metas'),
                ('🖥️ Desenvolvimento', '/desenvolvimento'),
                ('📝 Avaliação de Competência', '/ava_competencia')
            ]
            for label, rota in botoes:
                ui.button(label, on_click=lambda r=rota: ui.navigate.to(r)).classes(
                    'w-full mb-2 bg-white text-blue font-semibold hover:bg-gray-100 rounded-lg'
                )
            # Botão toggle à direita
            toggle_button = ui.button('☰').classes(
                'absolute top-4 right-[-20px] bg-white text-blue font-bold rounded-lg shadow'
            )

        # Conteúdo principal
        with ui.column().classes('flex-1 p-8 transition-all duration-300') as main_content:
            ui.label(titulo).classes('text-3xl font-bold text-blue-700 mb-6')
            with ui.card().classes('w-full p-6 bg-white shadow-lg rounded-xl'):
                conteudo_func()

    ui.image(resource_path('./images/sub_fachada.png')).classes("mx-auto rounded-2xl")

    # Função toggle com animação
    def toggle_sidebar():
        nonlocal sidebar_visible
        if sidebar_visible:
            sidebar.style('transform: translateX(-100%)')  # desliza para fora
            main_content.style('margin-left: 0')           # conteúdo ocupa todo espaço
            sidebar_visible = False
        else:
            sidebar.style('transform: translateX(0)')     # volta para posição original
            main_content.style('margin-left: 0')        # conteúdo volta para lado
            sidebar_visible = True

    toggle_button.on('click', lambda _: toggle_sidebar())

# --------- Páginas ---------
@ui.page('/')
def home():
    layout_com_menu("🏠 Menu Inicial", conteudo_menu_inicial)
    
@ui.page('/rh')
def rh():
    layout_com_menu("🧑‍🤝‍🧑 Gente e Gestão", conteudo_rh)

@ui.page('/comercial') 
def comercial():
    layout_com_menu("💼 Comercial", conteudo_comercial)

@ui.page('/operacoes')
def operacoes():
    layout_com_menu("🌐 Operações", conteudo_operacoes)

@ui.page('/atendimento')
def atendimento_cliente():
    layout_com_menu("🗣️ Atendimento ao Cliente", conteudo_atendimento_cliente)

@ui.page('/metas')
def metas():
    layout_com_menu("🎯 Metas", conteudo_metas)

@ui.page('/desenvolvimento')
def desenvolvimento():
    layout_com_menu("🖥️ Desenvolvimento", conteudo_desenvolvimento)

@ui.page('/ava_competencia')
def ava_competencia():
    layout_com_menu("📝 Avaliação de Competência", conteudo_ava_competencia)
# --------- Abrir navegador ---------

data_hoje = datetime.today()

print(">>> Iniciando app...")
print(f">>> Rodando em: {data_hoje}")

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path

ui.run(title="Indicadores - Wareline", reload=False, favicon=resource_path('images/icone_indicadores.ico'), host='0.0.0.0', port=20000)