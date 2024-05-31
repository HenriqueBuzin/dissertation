import graphene
from database import mongo_collection

class EnergyConsumptionType(graphene.ObjectType):
    id = graphene.String()
    street = graphene.String()
    date = graphene.String()
    time = graphene.String()
    consumptionKwhPerHour = graphene.String()  # Adjusted to camelCase

class WaterConsumptionType(graphene.ObjectType):
    id = graphene.Int()
    street = graphene.String()
    date = graphene.String()
    time = graphene.String()
    consumptionM3PerHour = graphene.String()  # Adjusted to camelCase

class Query(graphene.ObjectType):
    energy_consumption_data = graphene.List(
        EnergyConsumptionType,
        id=graphene.String(),
        street=graphene.String(),
        date=graphene.String(),
        time=graphene.String(),
        consumptionKwhPerHour=graphene.String(),  # Adjusted to camelCase
    )

    water_consumption_data = graphene.List(
        WaterConsumptionType,
        id=graphene.Int(),
        street=graphene.String(),
        date=graphene.String(),
        time=graphene.String(),
        consumptionM3PerHour=graphene.String()  # Adjusted to camelCase
    )

    def resolve_energy_consumption_data(self, info, **kwargs):
        query = {}
        for key in ['id', 'street', 'date', 'time']:
            if kwargs.get(key) is not None:
                query[key] = kwargs[key]
        
        if kwargs.get('consumptionKwhPerHour') is not None:
            query['consumption_kwh_per_hour'] = kwargs['consumptionKwhPerHour']
        else:
            query['consumption_kwh_per_hour'] = {'$exists': True}

        print(f"Query: {query}")  # Debug: Print the query being used

        data_query = mongo_collection.find(query)
        items = list(data_query)

        # Debug: Print the retrieved data from MongoDB
        for item in items:
            print(f"MongoDB Item: {item}")
            print(f"consumption_kwh_per_hour exists: {'consumption_kwh_per_hour' in item}")
            print(f"consumption_kwh_per_hour value: {item.get('consumption_kwh_per_hour', None)}")
        
        result = []
        for item in items:
            if 'consumption_kwh_per_hour' in item:
                result.append(EnergyConsumptionType(
                    id=str(item["id"]),
                    street=item.get("street", ""),
                    date=item.get("date", ""),
                    time=item.get("time", ""),
                    consumptionKwhPerHour=str(item['consumption_kwh_per_hour'])  # Ajustado para camelCase
                ))
        
        # Debug: Print the result before returning
        for res in result:
            print(f"GraphQL Result Item: {res}")

        return result

    def resolve_water_consumption_data(self, info, **kwargs):
        query = {}
        for key in ['id', 'street', 'date', 'time']:
            if kwargs.get(key) is not None:
                query[key] = kwargs[key]

        if kwargs.get('consumptionM3PerHour') is not None:
            query['consumption_m3_per_hour'] = kwargs['consumptionM3PerHour']

        print(f"Query: {query}")  # Debug: Print the query being used

        data_query = mongo_collection.find(query)
        items = list(data_query)

        # Debug: Print the retrieved data from MongoDB
        for item in items:
            print(f"MongoDB Item: {item}")
        
        result = [
            WaterConsumptionType(
                id=item["id"],
                street=item.get("street", ""),
                date=item.get("date", ""),
                time=item.get("time", ""),
                consumptionM3PerHour=str(item.get("consumption_m3_per_hour", ""))  # Ajustado para camelCase
            ) for item in items
        ]

        # Debug: Print the result before returning
        for res in result:
            print(f"GraphQL Result Item: {res}")

        return result

schema = graphene.Schema(query=Query)
