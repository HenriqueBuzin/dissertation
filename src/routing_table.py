import uio
import json

class RoutingTable:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}

    def read(self):
        try:
            with open(self.filename, 'r') as file:
                # Criar um objeto de arquivo io
                file_io = uio.open(file=file)

                # Carregar o conteúdo do arquivo JSON para uma estrutura de dados Python
                self.data = json.load(file_io)

        except OSError:
            print("Erro ao ler o arquivo.")

    def write(self):
        try:
            with open(self.filename, 'w') as file:
                # Criar um objeto de arquivo io
                file_io = uio.open(file=file, mode='w')

                # Salvar a estrutura de dados no arquivo JSON
                json.dump(self.data, file_io)

        except OSError:
            print("Erro ao escrever no arquivo.")
    
    def process(self):
        ips = [entry.get("ip") for entry in self.data]
        total_ips = len(ips)
        current_listen = 0  # Contador para controlar o número de conexões listen
        
        # Processar os IPs com base na ordem desejada
        processed_ips = self.cidr(ips)
        
        if len(processed_ips) > self.listen_value:
            processed_ips = self.vlsm(ips)
        
        if len(processed_ips) > self.listen_value:
            processed_ips = self.prefix_aggregation(ips)
        
        if len(processed_ips) > self.listen_value:
            processed_ips = self.route_summarization(ips)
        
        # Verificar se o objetivo foi alcançado
        if len(processed_ips) <= self.listen_value:
            # Atualizar os dados do IP no objeto self.data conforme necessário
            for i, entry in enumerate(self.data):
                entry["processed_ip"] = processed_ips[i]
                print("IP Processado:", processed_ips[i])
            
            # Chamar o método write() para salvar as alterações
            self.write()
            print("Processamento de IPs concluído com sucesso.")
        else:
            print("Não foi possível reduzir a tabela de IPs ao número desejado de conexões listen.")

    @staticmethod
    def cidr(ip, mask):
        ip_parts = ip.split('.')
        mask_parts = mask.split('.')
        
        network_address = []
        for i in range(4):
            network_address.append(str(int(ip_parts[i]) & int(mask_parts[i])))
        
        return '.'.join(network_address), mask

    @staticmethod
    def vlsm(subnets, hosts):
        networks = ['0.0.0.0/0']
        subnets = [int(hosts[i]) + 2 for i in range(len(subnets))]

        for subnet in subnets:
            new_networks = []
            for network in networks:
                network_address, subnet_mask = network.split('/')
                network_parts = network_address.split('.')
                
                # Incrementa o último octeto da rede para criar sub-redes
                for i in range(2 ** (32 - int(subnet))):
                    new_network_parts = network_parts[:]
                    new_network_parts[3] = str(int(new_network_parts[3]) + i)
                    new_network = '.'.join(new_network_parts) + '/' + str(subnet)
                    new_networks.append(new_network)

            networks = new_networks

        return [network.split('/')[0] for network in networks]

    @staticmethod
    def prefix_aggregation(networks):
        # Converter as redes para uma lista de tuplas (endereço, máscara)
        networks = [(net.split('/')[0], int(net.split('/')[1])) for net in networks]

        # Ordenar as redes com base no endereço IP
        networks.sort()

        aggregated_networks = []
        current_network = networks[0]

        for i in range(1, len(networks)):
            current_address, current_mask = current_network
            next_address, next_mask = networks[i]

            # Verificar se os dois prefixos podem ser agregados
            if current_address == next_address[:current_mask]:
                # Atualizar a máscara para a maior entre as duas redes
                current_network = (current_address, max(current_mask, next_mask))
            else:
                # Adicionar a rede atual à lista de redes agregadas
                aggregated_networks.append(f"{current_address}/{current_mask}")
                current_network = networks[i]

        # Adicionar a última rede à lista de redes agregadas
        aggregated_networks.append(f"{current_address}/{current_mask}")

        return aggregated_networks

    @staticmethod
    def route_summarization(networks):
        # Converter as redes para uma lista de tuplas (endereço, máscara)
        networks = [(net.split('/')[0], int(net.split('/')[1])) for net in networks]

        # Ordenar as redes com base no endereço IP
        networks.sort()

        summarized_networks = []
        current_network = networks[0]

        for i in range(1, len(networks)):
            current_address, current_mask = current_network
            next_address, next_mask = networks[i]

            # Verificar se os dois prefixos podem ser sumarizados
            if current_address == next_address[:current_mask]:
                # Atualizar a máscara para a menor entre as duas redes
                current_network = (current_address, min(current_mask, next_mask))
            else:
                # Adicionar a rede atual à lista de redes sumarizadas
                summarized_networks.append(f"{current_address}/{current_mask}")
                current_network = networks[i]

        # Adicionar a última rede à lista de redes sumarizadas
        summarized_networks.append(f"{current_address}/{current_mask}")

        return summarized_networks
