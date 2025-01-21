# http_server.py

from aiohttp import web
import logging
from aiohttp import ClientSession
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)

# Função para distribuir dados via HTTP usando round-robin
async def distribute_data_via_http(data_type, data, available_nodes, max_retries=3):
    nodes = available_nodes.get(data_type, [])
    if not nodes:
        logging.warning(f"HTTP: Nenhum nó disponível para o tipo de dado '{data_type}'.")
        return

    for attempt in range(max_retries):
        # Seleciona o próximo nó em um round-robin
        node = nodes.pop(0)
        nodes.append(node)  # Reinserir o nó no final da lista

        node_endpoint = node["node_endpoint"]
        try:
            async with ClientSession() as session:
                async with session.post(node_endpoint, json=data) as resp:
                    if resp.status == 200:
                        logging.info(f"HTTP: Dados enviados para o nó {node['node_id']} em {node_endpoint}")
                        return
                    else:
                        logging.error(f"HTTP: Falha ao enviar dados para o nó {node['node_id']} em {node_endpoint}. Status: {resp.status}")
        except Exception as e:
            logging.error(f"HTTP: Erro ao enviar dados para o nó {node['node_id']} em {node_endpoint}: {e}")

        logging.info(f"HTTP: Tentativa {attempt + 1} de {max_retries} falhou. Tentando próximo nó.")

    logging.error(f"HTTP: Falha ao distribuir dados para o tipo '{data_type}' após {max_retries} tentativas.")

# Endpoint para receber dados via HTTP
async def handle_receive_data(request, available_nodes):
    try:
        data = await request.json()
        data_type = data.get("type")
        data_content = data.get("data")

        if not data_type or not data_content:
            logging.warning("HTTP: Dados ou tipo ausente nos dados recebidos.")
            return web.json_response({"status": "Erro: Dados ou tipo ausente."}, status=400)

        logging.info(f"HTTP: Dados recebidos: {data}")

        # Distribuir os dados para um nó apropriado via HTTP
        await distribute_data_via_http(data_type, data, available_nodes)

        return web.json_response({"status": "HTTP: Dados recebidos com sucesso"})
    except Exception as e:
        logging.error(f"Erro no Servidor HTTP: {e}")
        return web.json_response({"status": "Erro no Servidor HTTP"}, status=500)

# Endpoint para registrar nós via HTTP
async def handle_register_node(request, available_nodes):
    try:
        data = await request.json()
        node_id = data.get("node_id")
        data_type = data.get("data_type")
        node_endpoint = data.get("node_endpoint")  # ex: "http://node_id:port/receive_data"

        if not node_id or not data_type or not node_endpoint:
            logging.warning("HTTP: Registro de nó recebido com dados incompletos.")
            return web.json_response({"status": "Erro: Dados de registro incompletos."}, status=400)

        # Adicionar o nó à lista de nós disponíveis para o tipo de dado
        node_info = {
            "node_id": node_id,
            "node_endpoint": node_endpoint
        }
        if data_type not in available_nodes:
            available_nodes[data_type] = []
        available_nodes[data_type].append(node_info)
        logging.info(f"HTTP: Nó registrado: {node_info} para o tipo {data_type}")

        return web.json_response({"status": "Nó registrado com sucesso."})
    except Exception as e:
        logging.error(f"Erro no Registro de Nó HTTP: {e}")
        return web.json_response({"status": "Erro no Registro de Nó HTTP"}, status=500)

# Iniciar o servidor HTTP
async def start_http_server(port, available_nodes):
    app = web.Application()
    app.router.add_post("/receive_data", lambda request: handle_receive_data(request, available_nodes))
    app.router.add_post("/register_node", lambda request: handle_register_node(request, available_nodes))

    logging.info(f"HTTP: Servidor rodando na porta {port}...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # Manter o servidor rodando
    await asyncio.get_event_loop().create_future()
