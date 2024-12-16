# Dockerfile
FROM node:23.4.0
WORKDIR /app
COPY package.json /app
RUN npm install
COPY coap_data_sender.js /app
CMD ["node", "coap_data_sender.js"]
