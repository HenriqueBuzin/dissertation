const express = require('express');
const { ApolloServer, gql } = require('apollo-server-express');
const axios = require('axios');

const app = express();
app.use(express.json());

// Definição do esquema GraphQL
const typeDefs = gql`
  type Query {
    _empty: String
  }

  type DataType {
    date: String
    time: String
    consumption: Float
  }

  type Mutation {
    createData(date: String, time: String, consumption: Float): DataType
  }
`;

// Resolvers para o GraphQL
const resolvers = {
  Query: {
    _empty: () => '',
  },
  Mutation: {
    createData: (parent, args) => {
      console.log("Dados recebidos na mutação:", args);
      return args;
    },
  },
};

// Inicializando o servidor Apollo com o esquema e resolvers
const graphqlServer = new ApolloServer({ typeDefs, resolvers });

async function startServer() {
  await graphqlServer.start();
  graphqlServer.applyMiddleware({ app });

  app.post('/webhook', async (req, res) => {
    const data = req.body;
    console.log("Dados recebidos via webhook:", data);

    // Ajuste para corresponder às chaves recebidas
    const graphqlQuery = {
      query: `
        mutation {
          createData(date: "${data.Date}", time: "${data.Time}", consumption: ${data.Consumption_kWh_per_minute}) {
            date
            time
            consumption
          }
        }
      `,
    };

    try {
      const response = await axios.post('http://localhost:5001/graphql', graphqlQuery);
      console.log("Dados enviados para o servidor GraphQL:", response.data);
      res.json({ status: "success", message: "Dados processados" });
    } catch (e) {
      console.error("Erro ao processar dados:", e);
      res.status(500).json({ status: "error", message: e.message });
    }
  });

  const PORT = 5001;
  app.listen(PORT, () => {
    console.log(`Servidor rodando em http://localhost:${PORT}`);
  });
}

startServer();
