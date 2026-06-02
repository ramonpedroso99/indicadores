from datetime import datetime
from collections import Counter
from nicegui import ui
import asyncio
from conexao import conectar_ao_banco

print(">>> Módulo atendimento_ao_cliente_method carregado!")

def conteudo_atendimento_cliente():

    async def buscar_avaliacoes(mes_ano: str):
        ano, mes = map(int, mes_ano.split('-'))
        data_inicio = datetime(ano, mes, 1)
        data_fim    = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)

        conn = await conectar_ao_banco()
        try:
            query = """
            SELECT satisfacao.descricao
            FROM soa_interacoes
            LEFT JOIN satisfacao ON satisfacao.id = soa_interacoes.satisfacao_id
            WHERE soa_interacoes.created >= $1
              AND soa_interacoes.created <  $2;
            """
            registros = await conn.fetch(query, data_inicio, data_fim)
        finally:
            await conn.close()

        return [r['descricao'] or 'Sem avaliação' for r in registros]

    # Interface
    ui.label('🔴 Pesquisa SOA - Satisfação dos atendimentos').classes('font-bold text-lg')
    ui.label('Medição mensal')
    ui.label('Resultado: Gerar o gráfico e contabilizar cada avaliação (Excelente, Sem avaliação e Péssimo).')

    ui.label("📈 Meta - Satisfação dos Atendimentos").classes('text-2xl font-bold mb-4')

    seletor_mes_ano = ui.input(
        "📅 Selecione o mês (YYYY-MM)",
        value=datetime.now().strftime('%Y-%m')
    ).on('blur', lambda _: asyncio.create_task(atualizar_grafico()))

    grafico = ui.echart({
        'title':  {'text': 'Avaliações por Satisfação'},
        'tooltip': {},
        'xAxis':  {'type': 'category', 'data': []},
        'yAxis':  {'type': 'value'},
        'series': [{'type': 'bar', 'data': []}],
    }).classes('w-full h-96')

    resultado_div   = ui.column().classes("mt-4")
    aviso_atend     = ui.label('').classes('text-red-600 font-semibold mt-2')
    spinner_atend   = ui.spinner('dots', size='lg').classes('mx-auto mt-2')
    spinner_atend.set_visibility(False)

    async def atualizar_grafico():
        aviso_atend.set_text('')
        spinner_atend.set_visibility(True)
        try:
            mes_ano    = seletor_mes_ano.value
            avaliacoes = await buscar_avaliacoes(mes_ano)
            contagem   = Counter(avaliacoes)

            excelente = avaliacoes.count('Excelente')
            pessimo   = avaliacoes.count('Péssimo')
            total     = excelente + pessimo

            categorias      = ['Excelente', 'Péssimo']
            dados_coloridos = [
                {'value': excelente, 'itemStyle': {'color': '#4CAF50'}},
                {'value': pessimo,   'itemStyle': {'color': '#F44336'}},
            ]

            grafico.options['title']['text']     = f'Satisfação em {mes_ano}'
            grafico.options['xAxis']['data']     = categorias
            grafico.options['series'][0]['data'] = dados_coloridos
            grafico.update()

            resultado_div.clear()
            with resultado_div:
                ui.label(f"📌 Total de Avaliações: {total}").classes("text-blue-600 font-bold mb-2")
                for cat in categorias:
                    qtd  = contagem.get(cat, 0)
                    perc = (qtd / total * 100) if total > 0 else 0
                    with ui.card().classes("rounded-2xl"):
                        ui.label(f"{cat}: {qtd} ({perc:.1f}%)").classes("font-semibold")

        except Exception as e:
            aviso_atend.set_text(f'❌ Erro ao carregar dados: {e}')
        finally:
            spinner_atend.set_visibility(False)

    ui.button(
        "Gerar Gráfico",
        on_click=lambda: asyncio.create_task(atualizar_grafico())
    ).classes('mt-4')
