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
        data_fim = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)

        try:
            conn = await conectar_ao_banco()

            query = """
            SELECT satisfacao.descricao
            FROM soa_interacoes
            LEFT JOIN satisfacao ON satisfacao.id = soa_interacoes.satisfacao_id
            WHERE 
                soa_interacoes.created >= $1
                AND soa_interacoes.created < $2;
            """

            registros = await conn.fetch(query, data_inicio, data_fim)
            await conn.close()

            return [r['descricao'] or 'Sem avaliação' for r in registros]

        except Exception as e:
            print(f'Erro ao buscar avaliações: {e}')
            return []

    # Interface com metas a serem atingidas
    ui.label('🔴 Pesquisa SOA - Satisfação dos atendimentos').classes('font-bold text-lg')
    ui.label('Medição mensal')
    ui.label('Resultado: Gerar o gráfico e contabilizar cada avaliação (Excelente, Sem avaliação e Péssimo).')


    ui.label("📈 Meta - Satisfação dos Atendimentos").classes('text-2xl font-bold mb-4')

    seletor_mes_ano = ui.input("📅 Selecione o mês (YYYY-MM)", value=datetime.now().strftime('%Y-%m')) \
        .on('blur', lambda e: asyncio.create_task(atualizar_grafico()))

    grafico = ui.echart({
        'title': {'text': 'Avaliações por Satisfação'},
        'tooltip': {},
        'xAxis': {'type': 'category', 'data': []},
        'yAxis': {'type': 'value'},
        'series': [{
            'type': 'bar',
            'data': [],
        }]
    }).classes('w-full h-96')
    
    resultado_div = ui.column().classes("mt-4")

    async def atualizar_grafico():
        try:
            mes_ano = seletor_mes_ano.value
            avaliacoes = await buscar_avaliacoes(mes_ano)
            
            excelente = avaliacoes.count('Excelente')
            #sem_avaliacao = avaliacoes.count('Sem Avaliação')  # cuidado com o nome exato
            pessimo = avaliacoes.count('Péssimo')

            total = excelente + pessimo

            #perc_excelente = (excelente / total * 100) if total > 0 else 0
            #perc_sem = (sem_avaliacao / total * 100) if total > 0 else 0
            #perc_pessimo = (pessimo / total * 100) if total > 0 else 0

            contagem = Counter(avaliacoes)

            categorias = ['Excelente', 'Péssimo']
            
            dados_coloridos = [
                {'value': excelente, 'itemStyle': {'color': '#4CAF50'}},
                #{'value': sem_avaliacao, 'itemStyle': {'color': '#9E9E9E'}},
                {'value': pessimo, 'itemStyle': {'color': '#F44336'}},
            ]

            #Vou deixar por enquanto desse jeito, comentado, futuramente se precisar usar
            #Os sem avaliação eu tenho o código pronto já...

            grafico.options['title']['text'] = f'Satisfação em {mes_ano}'
            grafico.options['xAxis']['data'] = categorias
            grafico.options['series'][0]['data'] = dados_coloridos
            grafico.update()

            

            resultado_div.clear()
            with resultado_div:
                ui.label(f"📌 Total de Avaliações: {total}").classes("text-blue-600 font-bold mb-2")
                for cat in categorias:
                    qtd = contagem.get(cat, 0)
                    perc = (qtd / total * 100) if total > 0 else 0
                    with ui.card().classes("rounded-2xl"):
                        ui.label(f"{cat}: {qtd} ({perc:.1f}%)").classes("font-semibold")

        except Exception as e:
            print(f"Erro ao atualizar gráfico: {e}")
            ui.notify(f"Erro ao gerar gráfico: {e}")

    ui.button("Gerar Gráfico", on_click=lambda: asyncio.create_task(atualizar_grafico())).classes('mt-4')
