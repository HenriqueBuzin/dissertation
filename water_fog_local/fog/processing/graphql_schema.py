import graphene
from database import mongo_collection

def create_consumption_type():
    return type('Consumption', (graphene.ObjectType,), {
        'id': graphene.String(),
        'street': graphene.String(),
        'date': graphene.String(),
        'consumptionKwhPerMinute': graphene.Float(),
        'type': graphene.String()
    })

def resolve_consumption_data(root, info, **kwargs):
    query = {}
    for key in ['id', 'street', 'date', 'consumption_kwh_per_minute', 'type']:
        if kwargs.get(key) is not None:
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

def create_query_type(Consumption):
    return type('Query', (graphene.ObjectType,), {
        'consumption_data': graphene.List(
            Consumption,
            id=graphene.String(),
            street=graphene.String(),
            date=graphene.String(),
            consumptionKwhPerMinute=graphene.Float(),
            type=graphene.String(),
            limit=graphene.Int(),
            offset=graphene.Int(),
            resolver=lambda self, info, **kwargs: resolve_consumption_data(self, info, **kwargs),
        )
    })

ConsumptionType = create_consumption_type()
QueryType = create_query_type(ConsumptionType)
schema = graphene.Schema(query=QueryType)
