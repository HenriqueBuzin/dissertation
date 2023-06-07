from server import Server
from routing_table import RoutingTable

def main():
    # Definir o valor de listen (número máximo de clientes em espera)
    listen_value = 10

    # Criar uma instância da tabela de roteamento
    routing_table = RoutingTable("routing_table.json")
    routing_table.listen_value = listen_value

    # Processar os IPs na tabela de roteamento
    routing_table.process()

    # Criar uma instância do servidor
    server = Server()

    # Definir o valor de listen (número máximo de clientes em espera)
    server.listen = listen_value

    # Iniciar o servidor
    server.start()

if __name__ == "__main__":
    main()
