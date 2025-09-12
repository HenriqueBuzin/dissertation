# utils/load_balancer.py

from ..network import get_available_port, create_or_get_bairro_network, create_or_get_lb_network
from ..docker_utils import get_docker_client, get_docker_errors
from ..general import normalize_container_name

# Portas internas fixas no container – visíveis apenas dentro da rede Docker
INTERNAL_HTTP_PORT = 5000
INTERNAL_COAP_PORT = 5683


def create_load_balancer(bairro, container_name, image, container_types):
    
    """
        Cria um Load Balancer (HTTP + CoAP) dedicado a *bairro*.

        O serviço interno do LB permanece ouvindo nas portas **5000** (HTTP) e
        **5683** (CoAP) dentro da rede Docker. Para facilitar testes externos, cada
        porta é publicada em uma porta aleatória livre do host.

        Passos executados:
            1. Escolhe duas portas livres no host (``get_available_port``).
            2. Garante/obtém duas redes:
            • **lb_net** – onde os LBs trocam metadados.
            • **<bairro>_net** – rede exclusiva do bairro.
            3. Cria o contêiner montando ``/var/run/docker.sock`` (modo *ro*) para
            descoberta dinâmica de peers.
            4. Conecta o contêiner à rede do bairro para alcançar fog‑nodes e medidores.

        Args:
            bairro: Nome do bairro (ex.: ``"Canasvieiras"``).
            container_name: Sufixo que compõe o nome do contêiner (ex.: ``"load_balancer"``).
            image: Imagem Docker contendo o serviço do LB.
            container_types: Mapeamento "tipo" → ``{"id": int}``; deve conter
                ``"load_balancer"``.

        Returns:
            tuple[int, int] | tuple[None, None]:
                ``(host_http_port, host_coap_port)`` em caso de sucesso;
                ``(None, None)`` se ocorrer erro.

        Raises:
            docker.errors.APIError: Erro propagado pela API do Docker durante criação
            ou conexão em redes.
    """

    client, APIError = get_docker_client(), get_docker_errors()[2]

    lb_label_id = container_types["load_balancer"]["id"]
    full_name   = f"{normalize_container_name(bairro)}_{container_name}_1"

    try:
        # Portas aleatórias NO HOST para depuração externa (não usadas internamente)
        host_http_port = get_available_port(proto="tcp")
        host_coap_port = get_available_port(proto="udp")

        # Redes Docker
        bairro_net = create_or_get_bairro_network(bairro)
        lb_net     = create_or_get_lb_network()

        # Variáveis de ambiente que o processo dentro do container usa
        env = {
            "HTTP_PORT":   str(INTERNAL_HTTP_PORT),   # mantém 5000
            "COAP_PORT":   str(INTERNAL_COAP_PORT),   # mantém 5683
            "DOCKER_HOST": "unix:///var/run/docker.sock",
            "LB_TYPE_ID":  str(lb_label_id),
            "SELF_NAME":   full_name,
        }

        # Cria o container; monta o socket Docker só‑leitura
        client.containers.run(
            image,
            name=full_name,
            detach=True,
            network=lb_net,
            volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"}},
            environment=env,
            ports={
                f"{INTERNAL_HTTP_PORT}/tcp": host_http_port,
                f"{INTERNAL_COAP_PORT}/udp": host_coap_port,
            },
            labels={"type": str(lb_label_id)},
        )

        # Conecta o LB também à rede específica do bairro
        client.networks.get(bairro_net).connect(full_name)

        print(f"[SUCESSO] Load Balancer '{full_name}' criado:")
        print(f"  • interno → http://{full_name}:{INTERNAL_HTTP_PORT}  (host {host_http_port})")
        print(f"  • interno → coap://{full_name}:{INTERNAL_COAP_PORT} (host {host_coap_port})")
        return host_http_port, host_coap_port

    except APIError as e:
        print(f"[ERRO] Falha ao criar Load Balancer '{full_name}': {e}")
        return None, None
