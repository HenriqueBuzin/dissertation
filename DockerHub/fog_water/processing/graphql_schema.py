# processing/graphql_schema.py

import graphene
from processing.database import mongo_collection

class EnergyConsumptionType(graphene.ObjectType):
    id = graphene.String()
    street = graphene.String()
    date = graphene.String()
    time = graphene.String()
    consumptionKwhPerHour = graphene.String()

class WaterConsumptionType(graphene.ObjectType):
    id = graphene.Int()
    street = graphene.String()
    date = graphene.String()
    time = graphene.String()
    consumptionM3PerHour = graphene.String()

class Query(graphene.ObjectType):
    energy_consumption_data = graphene.List(
        EnergyConsumptionType,
        id=graphene.String(),
        street=graphene.String(),
        date=graphene.String(),
        time=graphene.String(),
        consumptionKwhPerHour=graphene.String()
    )

    water_consumption_data = graphene.List(
        WaterConsumptionType,
        id=graphene.Int(),
        street=graphene.String(),
        date=graphene.String(),
        time=graphene.String(),
        consumptionM3PerHour=graphene.String()
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

        print(f"Query: {query}", flush=True)

        data_query = mongo_collection.find(query)
        items = list(data_query)

        for item in items:
            print(f"MongoDB Item: {item}", flush=True)
            print(f"consumption_kwh_per_hour exists: {'consumption_kwh_per_hour' in item}", flush=True)
            print(f"consumption_kwh_per_hour value: {item.get('consumption_kwh_per_hour', None)}", flush=True)
        
        result = []
        for item in items:
            if 'consumption_kwh_per_hour' in item:
                result.append(EnergyConsumptionType(
                    id=str(item["id"]),
                    street=item.get("street", ""),
                    date=item.get("date", ""),
                    time=item.get("time", ""),
                    consumptionKwhPerHour=str(item['consumption_kwh_per_hour'])
                ))
        
        for res in result:
            print(f"GraphQL Result Item: {res}", flush=True)

        return result

    def resolve_water_consumption_data(self, info, **kwargs):
        query = {}
        for key in ['id', 'street', 'date', 'time']:
            if kwargs.get(key) is not None:
                query[key] = kwargs[key]

        if kwargs.get('consumptionM3PerHour') is not None:
            query['consumption_m3_per_hour'] = kwargs['consumptionM3PerHour']
        else:
            query['consumption_m3_per_hour'] = {'$exists': True}

        print(f"Query: {query}", flush=True)

        data_query = mongo_collection.find(query)
        items = list(data_query)

        for item in items:
            print(f"MongoDB Item: {item}", flush=True)
        
        result = [
            WaterConsumptionType(
                id=item["id"],
                street=item.get("street", ""),
                date=item.get("date", ""),
                time=item.get("time", ""),
                consumptionM3PerHour=str(item.get("consumption_m3_per_hour", ""))
            ) for item in items
        ]

        for res in result:
            print(f"GraphQL Result Item: {res}", flush=True)

        return result

schema = graphene.Schema(query=Query)
