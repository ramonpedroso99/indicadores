from nicegui import ui
from datetime import date, datetime
import asyncio
from conexao import conectar_ao_banco

print(">>> Módulo comercial_method carregado!")

def conteudo_comercial():
    
    async def tentar_conexao(tentativas=3, intervalo=2):
        for tentativa in range(1, tentativas + 1):
            try:
                conn = await conectar_ao_banco()
                return conn
            except Exception as e:
                print(f"Tentativa {tentativa}/{tentativas} falhou: {e}")
                if tentativa == tentativas:
                    raise e
                await asyncio.sleep(intervalo)

    async def contar_propostas(data_inicio, data_fim):
        conn = await tentar_conexao()

        query_total = """
            WITH RankedPropostas AS (
                SELECT
                    propcom.cliente_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY propcom.cliente_id
                        ORDER BY
                            CASE WHEN LOWER(propcom_status.descricao) = 'aceita' THEN 1 ELSE 2 END,
                            propcom.updated DESC
                    ) AS rn
                FROM propcom
                JOIN propcom_status ON propcom_status.id = propcom.propcom_status_id
                WHERE propcom.updated BETWEEN $1 AND $2
                AND propcom.propcom_modelo_id = '90'
            )
            SELECT COUNT(*) FROM RankedPropostas WHERE rn = 1;
        """

        query_aceitas = """
            WITH RankedPropostas AS (
                SELECT
                    propcom.cliente_id,
                    propcom_status.descricao AS status_proposta,
                    ROW_NUMBER() OVER (
                        PARTITION BY propcom.cliente_id
                        ORDER BY
                            CASE WHEN LOWER(propcom_status.descricao) = 'aceita' THEN 1 ELSE 2 END,
                            propcom.updated DESC
                    ) AS rn
                FROM propcom
                JOIN propcom_status ON propcom_status.id = propcom.propcom_status_id
                WHERE propcom.updated BETWEEN $1 AND $2
                AND propcom.propcom_modelo_id = '90'
            )
            SELECT COUNT(*) FROM RankedPropostas
            WHERE rn = 1 AND LOWER(status_proposta) = 'aceita';
        """

        try:
            total  = await conn.fetchval(query_total,  data_inicio, data_fim)
            aceitas = await conn.fetchval(query_aceitas, data_inicio, data_fim)
        finally:
            await conn.close()
        return total, aceitas

    # Interface com metas a serem atingidas
    ui.label('🔴 Prospects - Conversão').classes('font-bold text-lg')
    ui.label('Medição anual, últimos 12 meses')
    ui.label('Resultado: Dividir o número de aceitas pelo total de propostas, e terá a porcentagem de conversão.')


    ui.label('🤝 Meta - Prospects Conversão').classes('text-3xl font-bold text-black -700 mb-6')

    with ui.card().classes('p-6 bg-white rounded-xl shadow-lg'):
        with ui.row().classes('gap-4 mb-4'):
            ui.label('📅 Data Início')
            data_inicio = ui.date(value=date.today().replace(day=1)).classes('w-40')
            ui.label('📅 Data Fim')
            data_fim = ui.date(value=date.today()).classes('w-40')

        with ui.card().classes("rounded-2xl"):
            spinner = ui.spinner(size='lg').classes('mt-2').style('display:none')
            resultado_texto = ui.label('').classes('text-lg font-semibold mt-2')
            
    container_notificacoes = ui.column()

    async def buscar_dados(container):
        try:
            spinner.style('display:block')
            inicio = data_inicio.value
            if isinstance(inicio, str):
                inicio = datetime.strptime(inicio, '%Y-%m-%d').date()
            fim = data_fim.value
            if isinstance(fim, str):
                fim = datetime.strptime(fim, '%Y-%m-%d').date()
                
            total, aceitas = await contar_propostas(inicio, fim)
            porcentagem = (aceitas / total * 100) if total > 0 else 0
            resultado_texto.text = f'📊 Total: {total} | ✅ Aceitas: {aceitas} | 📈 Aceitação: {porcentagem:.2f}%'

            with container:
                ui.notify('Consulta concluída com sucesso!', type='positive')

        except Exception as e:
            resultado_texto.text = f'Erro: {e}'
            with container:
                ui.notify(f'Erro: {e}', type='negative')

        finally:
            spinner.style('display:none')

    ui.button('Buscar Propostas', on_click=lambda: asyncio.create_task(buscar_dados(container_notificacoes))).classes(
        'mt-2 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded shadow'
        )
