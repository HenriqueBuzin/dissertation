import graphene
from database import mongo_collection
from bson import ObjectId

class ConsumptionType(graphene.ObjectType):
    id = graphene.String()
    street = graphene.String()
    date = graphene.String()
    consumptionKwhPerMinute = graphene.Float()
    type = graphene.String()

class Query(graphene.ObjectType):
    consumption_data = graphene.List(
        ConsumptionType,
        id=graphene.String(),
        street=graphene.String(),
        date=graphene.String(),
        consumptionKwhPerMinute=graphene.Float(),
        type=graphene.String(),
        limit=graphene.Int(),
        offset=graphene.Int(),
    )

    def resolve_consumption_data(self, info, **kwargs):
        query = {}
        for key in ['id', 'street', 'date', 'consumption_kwh_per_minute', 'type']:
            if kwargs.get(key) is not None:
                if key == 'id':
                    query[key] = ObjectId(kwargs[key])
                else:
                    query[key] = kwargs[key]

        data_query = mongo_collection.find(query)
        offset = kwargs.get('offset', None)
        limit = kwargs.get('limit', None)
        if offset is not None:
            data_query = data_query.skip(offset)
        if limit is not None:
            data_query = data_query.limit(limit)

        return [
            {
                'id': str(item["id"]),
                'street': item.get("street", ""),
                'date': item["date"],
                'consumptionKwhPerMinute': item["consumption_kwh_per_minute"],
                'type': item["type"]
            } for item in data_query
        ]

schema = graphene.Schema(query=Query)
