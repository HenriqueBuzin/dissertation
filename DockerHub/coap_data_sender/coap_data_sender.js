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

// Ajustar a URL para garantir que não tenha "/receive_data" indevidamente
const coapUrl = new URL(COAP_SERVER_URL.replace("/receive_data", ""));
const uniqueId = instanceData.id;
const street = instanceData.street;

console.log("### Configurações ###");
console.log(`COAP_SERVER_URL: ${coapUrl.href}`);
console.log(`Hostname: ${coapUrl.hostname}`);
console.log(`Porta: ${coapUrl.port}`);
console.log(`CSV_URL: ${CSV_URL}`);
console.log(`INSTANCE_DATA: ${JSON.stringify(instanceData)}`);
console.log(`SEND_INTERVAL: ${SEND_INTERVAL}s`);

// Função para registrar o medidor no nó primário via CoAP
async function registerMeter(meterType) {
    return new Promise((resolve) => {
        const req = coap.request({
            method: "POST",
            hostname: coapUrl.hostname,
            pathname: "/register_meter",
            port: coapUrl.port,
        });

        const payload = JSON.stringify({ id: uniqueId, street: street, type: meterType });
        req.setOption("Content-Format", "application/json");
        req.write(payload);

        console.log(`Registrando medidor na URL CoAP: ${coapUrl.href}/register_meter com payload:`, payload);

        req.on("response", (res) => {
            const responseText = res.payload.toString();
            console.log(`Resposta do nó primário: ${res.code} - ${responseText}`);
            if (res.code.toString().startsWith("2.0")) {
                console.log(`Medidor ${uniqueId} (${meterType}) registrado com sucesso.`);
                resolve(true);
            } else {
                console.warn(`Falha no registro do medidor ${uniqueId}. Tentando novamente...`);
                resolve(false);
            }
        });

        req.on("error", (err) => {
            console.error("Erro ao registrar medidor:", err);
            resolve(false);
        });

        req.end();
    });
}

// Função para baixar e processar o CSV
async function downloadCsv(url) {
    try {
        console.log(`Baixando CSV de ${url}...`);
        const response = await axios.get(url);
        const lines = response.data.split("\n");

        console.log("Primeiras 5 linhas do CSV baixado:");
        for (let i = 0; i < Math.min(5, lines.length); i++) {
            console.log(lines[i]);
        }

        // Processar CSV
        const headers = lines.shift().split(";").map(header => header.trim());
        const data = lines
            .filter(line => line.trim())
            .map(line => {
                const values = line.split(";").map(value => value.trim());
                return headers.reduce((acc, header, index) => {
                    acc[header] = values[index] || null;
                    return acc;
                }, {});
            });

        // Detectar tipo do medidor
        let meterType = "desconhecido";
        if (headers.includes("consumption_m3_per_hour")) {
            meterType = "water";
        } else if (headers.includes("consumption_kwh_per_hour")) {
            meterType = "energy";
        }

        console.log(`Tipo de medidor detectado: ${meterType}`);
        return { data, meterType };
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
        pathname: "/receive_data",  // 🔧 CORRIGIDO!
        port: coapUrl.port, 
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
    console.log("Baixando e processando o CSV...");
    const { data, meterType } = await downloadCsv(CSV_URL);

    console.log("Registrando medidor no nó primário...");
    while (!(await registerMeter(meterType))) {
        console.log("Tentando novamente em 5 segundos...");
        await new Promise(resolve => setTimeout(resolve, 5000));
    }

    for (const dataEntry of data) {
        if (!dataEntry.date || !dataEntry.time) {
            console.warn("Aviso: Linha com dados incompletos ignorada:", dataEntry);
            continue;
        }

        const dataToSend = {
            type: meterType,
            id: uniqueId,
            street: street,
            ...dataEntry,
        };

        console.log("Enviando dados:", dataToSend);
        sendDataCoap(dataToSend);

        await new Promise(resolve => setTimeout(resolve, SEND_INTERVAL * 1000));
    }

    console.log("Envio concluído com sucesso!");
}

main().catch((err) => {
    console.error("Erro fatal:", err);
    process.exit(1);
});
