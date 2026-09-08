from elastic.configuration import get_elasticsearch_client
from test_bench_service.utilities.models import SkewedDataRecord


def gnn_vector_search(skewed_records: list[SkewedDataRecord], dataset_id: str):

    client = get_elasticsearch_client()

    body = []

    for record in skewed_records:

        body.append({'index': dataset_id})
        body.append({
            'knn': {
                "field": "graphing_vector",
                'query_vector': record.graph,
                'k': 5,
                'num_candidates': 10
            },
            '_source': ['id']
        })

    return client.msearch(body=body)


from elastic.configuration import get_elasticsearch_client
from generator.embeddings import serialize_record

def vector_matching(records, model, dataset_id):

    client = get_elasticsearch_client()

    body = []

    for record in records:
        record = serialize_record(record)

        embedding = model.encode(record, convert_to_tensor=True, show_progress_bar=False).tolist()

        body.append({'index': dataset_id})
        body.append({
            "knn": {
                "field": "embedding_vector",
                "query_vector": embedding,
                "k": 5,
                "num_candidates": 200
            },
        })
    return client.msearch(body=body)