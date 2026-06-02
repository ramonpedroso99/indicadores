from nicegui import ui
import asyncio
from datetime import datetime
from collections import Counter
from conexao import conectar_ao_banco

print(">>> Módulo operacoes_method carregado!")

def conteudo_operacoes():

    async def buscar_avaliacoes(mes_ano: str):
        conn = await conectar_ao_banco()
        try:
            query = """
            SELECT satisfacao.descricao
            FROM relatorio_viagens_historico_avaliacoes rha
            LEFT JOIN satisfacao ON satisfacao.id = rha.satisfacao_id
            WHERE TO_CHAR(rha.created, 'YYYY-MM') = $1;
            """
            rows = await conn.fetch(query, mes_ano)
        finally:
            await conn.close()
        return [row['descricao'] for row in rows]

    async def contar_viagens(mes_ano: str):
        ano, mes = mes_ano.split('-')
        data_inicio = datetime.strptime(f'{ano}-{mes}-01', '%Y-%m-%d')
        if mes == '12':
            data_fim = datetime.strptime(f'{int(ano)+1}-01-01', '%Y-%m-%d')
        else:
            data_fim = datetime.strptime(f'{ano}-{int(mes)+1:02d}-01', '%Y-%m-%d')

        conn = await conectar_ao_banco()
        try:
            query = """
            SELECT COUNT(DISTINCT rha.relatorio_viagem_id) AS total
            FROM relatorio_viagens_historico_avaliacoes rha
            WHERE rha.created >= $1 AND rha.created < $2;
            """
            row = await conn.fetchrow(query, data_inicio, data_fim)
        finally:
            await conn.close()
        return row['total']

    # Interface
    ui.label('🔴 Pesquisa - Viagem').classes('font-bold text-lg')
    ui.label('Medição mensal')
    ui.label('Resultado: Gerar o gráfico e contar quantos itens em cada avaliação (Excelente, Bom, Ok, Ruim e Péssimo).')

    ui.label("📈 Meta - Pesquisa Viagem").classes('text-2xl font-bold mb-4')

    with ui.card().classes("rounded-2xl"):
        label_total_viagens    = ui.label("").classes('text-lg mt-2 font-bold')
        label_perc_excelente   = ui.label("").classes("text-lg mt-2 font-bold").style("color: #006400;")
        label_perc_bom         = ui.label("").classes("text-lg mt-2 font-bold text-green")
        label_perc_ok          = ui.label("").classes("text-lg mt-2 font-bold text-yellow")
        label_perc_ruim        = ui.label("").classes("text-lg mt-2 font-bold text-orange")
        label_perc_pessimo     = ui.label("").classes("text-lg mt-2 font-bold text-red")

    seletor_mes_ano = ui.input(
        "📅 Selecione o mês (YYYY-MM)",
        value=datetime.now().strftime('%Y-%m')
    ).on('blur', lambda e: asyncio.create_task(atualizar_grafico()))

    grafico = ui.echart({
        'title':  {'text': 'Avaliações por Satisfação'},
        'tooltip': {},
        'xAxis':  {'type': 'category', 'data': []},
        'yAxis':  {'type': 'value'},
        'series': [{'type': 'bar', 'data': []}],
    }).classes('w-full h-96')

    aviso_operacoes = ui.label('').classes('text-red-600 font-semibold mt-2')
    spinner_operacoes = ui.spinner('dots', size='lg').classes('mx-auto mt-2')
    spinner_operacoes.set_visibility(False)

    async def atualizar_grafico():
        aviso_operacoes.set_text('')
        spinner_operacoes.set_visibility(True)
        try:
            mes_ano    = seletor_mes_ano.value
            avaliacoes = await buscar_avaliacoes(mes_ano)
            contagem   = Counter(avaliacoes)

            excelente = avaliacoes.count('Excelente')
            bom       = avaliacoes.count('Bom')
            ok        = avaliacoes.count('Ok')
            ruim      = avaliacoes.count('Ruim')
            pessimo   = avaliacoes.count('Péssimo')
            total     = excelente + bom + ok + ruim + pessimo

            if total == 0:
                aviso_operacoes.set_text('Nenhuma avaliação encontrada para este período.')
                return

            categorias     = ['Excelente', 'Bom', 'Ok', 'Ruim', 'Péssimo']
            cores          = {
                'Excelente': '#4CAF50',
                'Bom':       '#8BC34A',
                'Ok':        '#FFC107',
                'Ruim':      '#FF9800',
                'Péssimo':   '#F44336',
            }
            dados_coloridos = [
                {'value': contagem.get(cat, 0), 'itemStyle': {'color': cores[cat]}}
                for cat in categorias
            ]

            grafico.options['title']['text']       = f'Avaliações em {mes_ano}'
            grafico.options['xAxis']['data']       = categorias
            grafico.options['series'][0]['data']   = dados_coloridos
            grafico.update()

            total_viagens = await contar_viagens(mes_ano)
            label_total_viagens.text  = f"✈️ Total de viagens no mês: {total_viagens}"
            label_perc_excelente.text = f"Excelente: {excelente} | {excelente/total*100:.1f}%"
            label_perc_bom.text       = f"Bom: {bom} | {bom/total*100:.1f}%"
            label_perc_ok.text        = f"Ok: {ok} | {ok/total*100:.1f}%"
            label_perc_ruim.text      = f"Ruim: {ruim} | {ruim/total*100:.1f}%"
            label_perc_pessimo.text   = f"Péssimo: {pessimo} | {pessimo/total*100:.1f}%"

        except Exception as e:
            aviso_operacoes.set_text(f'❌ Erro ao carregar dados: {e}')
        finally:
            spinner_operacoes.set_visibility(False)

    ui.button(
        "Gerar Gráfico",
        on_click=lambda: asyncio.create_task(atualizar_grafico())
    ).classes('mt-4')
