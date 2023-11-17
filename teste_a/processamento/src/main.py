import graphene
from flask import Flask
from flask_graphql import GraphQLView
from collections.abc import MutableMapping

# Definição de Tipo para os Dados
class DataType(graphene.ObjectType):
    date = graphene.String()
    time = graphene.String()
    consumption = graphene.Float()

# Classe para a Mutação
class CreateData(graphene.Mutation):
    class Arguments:
        date = graphene.String(required=True)
        time = graphene.String(required=True)
        consumption = graphene.Float(required=True)

    data = graphene.Field(lambda: DataType)

    def mutate(root, info, date, time, consumption):
        # Aqui, você adicionaria lógica para armazenar os dados
        return DataType(date=date, time=time, consumption=consumption)

# Definição do Esquema GraphQL
class Mutation(graphene.ObjectType):
    create_data = CreateData.Field()

schema = graphene.Schema(mutation=Mutation)

# Configuração do Servidor Flask
app = Flask(__name__)
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Habilita a interface GraphiQL
    )
)

# Execução do Servidor
if __name__ == '__main__':
    app.run(debug=True)
