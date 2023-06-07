import uasyncio as asyncio
import usocket as socket

class Server:
    def __init__(self):
        self.running = False
        self.server_socket = None
        self.client_sockets = []
        self._listen = 5

    @property
    def listen(self):
        return self._listen

    @listen.setter
    def listen(self, backlog):
        if self.running:
            raise ValueError("Não é possível alterar o valor de listen enquanto o servidor estiver em execução.")
        self._listen = backlog

    async def start(self):
        self.running = True
        print("Servidor iniciado")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 8080))
        self.server_socket.listen(self.listen)

        while self.running:
            await self.listen()

    def stop(self):
        self.running = False
        print("Servidor parado")

        self.server_socket.close()
        for client_socket in self.client_sockets:
            client_socket.close()

    async def listen(self):
        loop = asyncio.get_event_loop()

        try:
            client_socket, client_addr = self.server_socket.accept()
            client_socket.setblocking(False)
            self.client_sockets.append(client_socket)
            print("Novo cliente conectado:", client_addr)

            loop.create_task(self.process(client_socket))
        except OSError:
            pass

    async def process(self, client_socket):
        try:
            data = client_socket.recv(1024)
            if data:
                print("Dados recebidos:", data)
                # Lógica para processar os dados recebidos

                # Exemplo de envio de resposta
                response = b"Recebido: " + data
                await self.send(client_socket, response)
            else:
                print("Cliente desconectado")
                self.client_sockets.remove(client_socket)
                client_socket.close()
        except socket.error as e:
            print("Erro ao receber dados do cliente:", e)

    async def send(self, client_socket, data):
        try:
            client_socket.sendall(data)
            print("Dados enviados:", data)
            # Lógica para processar a resposta do cliente, se necessário
        except socket.error as e:
            print("Erro ao enviar dados:", e)
