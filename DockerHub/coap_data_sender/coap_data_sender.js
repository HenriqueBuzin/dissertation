// coap_data_sender.js 

const coap = require('coap');
const axios = require('axios');

// Carregar variáveis de ambiente
const COAP_SERVER_URL = process.env.COAP_SERVER_URL;
const CSV_URL = process.env.CSV_URL;
const INSTANCE_DATA = process.env.INSTANCE_DATA;
const SEND_INTERVAL = parseInt(process.env.SEND_INTERVAL || "1", 10);

if (!COAP_SERVER_URL || !CSV_URL || !INSTANCE_DATA) {
    console.error("Erro: Variáveis de ambiente obrigatórias não definidas.");
    process.exit(1);
}

let instanceData;
try {
    instanceData = JSON.parse(INSTANCE_DATA);
} catch (err) {
    console.error("Erro ao processar INSTANCE_DATA:", err);
    process.exit(1);
}

const coapUrl = new URL(COAP_SERVER_URL);
const uniqueId = instanceData.id;
const street = instanceData.street;

console.log("### Configurações ###");
console.log(`COAP_SERVER_URL: ${COAP_SERVER_URL}`);
console.log(`Hostname: ${coapUrl.hostname}`);
console.log(`Porta: ${coapUrl.port}`);
console.log(`Pathname: ${coapUrl.pathname}`);
console.log(`CSV_URL: ${CSV_URL}`);
console.log(`INSTANCE_DATA: ${JSON.stringify(instanceData)}`);
console.log(`SEND_INTERVAL: ${SEND_INTERVAL}s`);

// Função para baixar e processar o CSV
async function downloadCsv(url) {
    try {
        console.log(`Baixando CSV de ${url}...`);
        const response = await axios.get(url);
        const lines = response.data.split("\n");

        // Depuração: Imprimir as primeiras linhas para verificar o delimitador
        console.log("Primeiras 5 linhas do CSV baixado:", flush=true);
        for (let i = 0; i < Math.min(5, lines.length); i++) {
            console.log(lines[i]);
        }

        // Usar o delimitador correto ';'
        const headers = lines.shift().split(";").map(header => header.trim());
        const data = lines
            .filter((line) => line.trim())
            .map((line) => {
                const values = line.split(";").map(value => value.trim());
                return headers.reduce((acc, header, index) => {
                    acc[header] = values[index] || null;
                    return acc;
                }, {});
            });

        console.log("CSV processado com sucesso:", data);
        return data;
    } catch (error) {
        console.error("Erro ao baixar ou processar o CSV:", error);
        process.exit(1);
    }
}

// Função para enviar dados via CoAP
function sendDataCoap(data) {
    const req = coap.request({
        method: "POST",
        hostname: coapUrl.hostname,
        pathname: coapUrl.pathname,
        port: coapUrl.port, // Porta definida na URL
    });

    req.setOption("Content-Format", "application/json");
    req.write(JSON.stringify(data));

    req.on("response", (res) => {
        console.log(`Resposta recebida: ${res.code} - ${res.payload.toString()}`);
    });

    req.on("error", (err) => {
        console.error("Erro ao enviar dados via CoAP:", err);
    });

    req.end();
}

// Função principal
async function main() {
    const dataList = await downloadCsv(CSV_URL);

    for (const data of dataList) {
        // Verificar se os campos esperados estão presentes
        if (!data.date || !data.time) {
            console.warn("Aviso: Linha com dados incompletos ignorada:", data);
            continue;
        }

        const dataToSend = {
            type: "consumption",
            id: uniqueId,
            street: street,
            ...data,
        };

        console.log("Enviando dados:", dataToSend);
        sendDataCoap(dataToSend);

        // Aguardar o intervalo definido
        await new Promise((resolve) => setTimeout(resolve, SEND_INTERVAL * 1000));
    }

    console.log("Envio concluído com sucesso!");
}

main().catch((err) => {
    console.error("Erro fatal:", err);
    process.exit(1);
});
