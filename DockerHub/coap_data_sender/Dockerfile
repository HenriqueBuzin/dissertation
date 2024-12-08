# Dockerfile para CoAP Sender em Node.js
FROM node:16

WORKDIR /app

# Instalar dependências
COPY package.json /app
RUN npm install

# Copiar o script para o contêiner
COPY coap_data_sender.js /app

# Comando de inicialização
CMD ["node", "coap_data_sender.js"]
