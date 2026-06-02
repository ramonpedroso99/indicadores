from nicegui import ui
import asyncio
from datetime import datetime
from collections import Counter
from conexao import conectar_ao_banco

print(">>> Módulo operacoes_method carregado!")

# ---------- CONEXÃO COM O BANCO ----------
def conteudo_operacoes():

    # ---------- CONSULTA DE AVALIAÇÕES ----------
    async def buscar_avaliacoes(mes_ano: str):
        conn = await conectar_ao_banco()
        query = """
        SELECT
            satisfacao.descricao
        FROM relatorio_viagens_historico_avaliacoes rha
        LEFT JOIN satisfacao ON satisfacao.id = rha.satisfacao_id
        WHERE TO_CHAR(rha.created, 'YYYY-MM') = $1;
        """
        rows = await conn.fetch(query, mes_ano)
        await conn.close()
        return [row['descricao'] for row in rows]
    
    # ---------- ATUALIZAR GRÁFICO ----------   
    async def atualizar_grafico():
        try:
            mes_ano = seletor_mes_ano.value
            avaliacoes = await buscar_avaliacoes(mes_ano)
            contagem = Counter(avaliacoes)

            excelente = avaliacoes.count('Excelente')
            bom = avaliacoes.count('Bom')
            ok = avaliacoes.count('Ok')
            ruim = avaliacoes.count('Ruim')
            pessimo = avaliacoes.count('Péssimo')

            total = excelente + bom + ok + ruim + pessimo

            perc_excelente = (excelente / total * 100)
            perc_bom = (bom / total * 100)
            perc_ok = (ok / total * 100)
            perc_ruim = (ruim / total * 100)
            perc_pessimo = (pessimo / total * 100)

            categorias = ['Excelente', 'Bom', 'Ok', 'Ruim', 'Péssimo']
            #dados = [contagem.get(cat, 0) for cat in categorias]

            cores = {
            'Excelente': '#4CAF50',  # verde
            'Bom': '#8BC34A',        # verde claro
            'Ok': '#FFC107',         # amarelo
            'Ruim': '#FF9800',       # laranja
            'Péssimo': '#F44336',    # vermelho
            }

            dados_coloridos = [
            {
                'value': contagem.get(cat, 0),
                'itemStyle': {'color': cores[cat]}
            }
            for cat in categorias
            ]

            grafico.options['title']['text'] = f'Avaliações em {mes_ano}'
            grafico.options['xAxis']['data'] = categorias
            grafico.options['series'][0]['data'] = dados_coloridos
            grafico.update()

            total_viagens = await contar_viagens(mes_ano)
            label_total_viagens.text = f"✈️ Total de viagens no mês: {total_viagens}"
            label_perc_excelente.text = f"Excelente: {excelente} | {perc_excelente:.1f}%"
            label_perc_bom.text = f"Bom: {bom} | {perc_bom:.1f}%"
            label_perc_ok.text = f"Ok: {ok} | {perc_ok:.1f}%"
            label_perc_ruim.text = f"Ruim: {ruim} | {perc_ruim:.1f}%"
            label_perc_pessimo.text = f"Péssimo: {pessimo} | {perc_pessimo:.1f}%"

        except Exception as e:
            print(f"Erro ao atualizar gráfico: {e}")

    # Interface com metas a serem atingidas
    
    ui.label('🔴 Pesquisa - Viagem').classes('font-bold text-lg')
    ui.label('Medição mensal')
    ui.label('Resultado: Gerar o gráfico e contar quantos itens em cada avaliação (Excelente, Bom, Ok, Ruim e Péssimo).')    
    
    # ---------- INTERFACE ----------
    ui.label("📈 Meta - Pesquisa Viagem").classes('text-2xl font-bold mb-4')
    with ui.card().classes("rounded-2xl"):
        label_total_viagens = ui.label("").classes('text-lg mt-2 font-bold')
        label_perc_excelente = ui.label("").classes("text-lg mt-2 font-bold").style("color: #006400;")
        label_perc_bom = ui.label("").classes("text-lg mt-2 font-bold text-green")
        label_perc_ok = ui.label("").classes("text-lg mt-2 font-bold text-yellow")
        label_perc_ruim = ui.label("").classes("text-lg mt-2 font-bold text-orange")
        label_perc_pessimo = ui.label("").classes("text-lg mt-2 font-bold text-red")


    seletor_mes_ano = ui.input("📅 Selecione o mês (YYYY-MM)", value=datetime.now().strftime('%Y-%m')).on('blur', lambda e: asyncio.create_task(atualizar_grafico()))

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

    ui.button("Gerar Gráfico", on_click=lambda: asyncio.create_task(atualizar_grafico())).classes('mt-4')

    async def contar_viagens(mes_ano: str):
        conn = await conectar_ao_banco()
        query = """
        SELECT COUNT(DISTINCT rha.relatorio_viagem_id) AS total
        FROM relatorio_viagens_historico_avaliacoes rha
        WHERE rha.created >= $1 AND rha.created < $2;
        """
        from datetime import datetime

        ano, mes = mes_ano.split('-')
        data_inicio = datetime.strptime(f'{ano}-{mes}-01', '%Y-%m-%d')
        if mes == '12':
            data_fim = datetime.strptime(f'{int(ano)+1}-01-01', '%Y-%m-%d')
        else:
            proximo_mes = int(mes) + 1
            data_fim = datetime.strptime(f'{ano}-{proximo_mes:02d}-01', '%Y-%m-%d')

        row = await conn.fetchrow(query, data_inicio, data_fim)
        await conn.close()
        return row['total']
