# Dockerfile
FROM node:22.12.0-slim
WORKDIR /app
COPY package.json /app
RUN npm install
COPY coap_data_sender.js /app
CMD ["node", "coap_data_sender.js"]
