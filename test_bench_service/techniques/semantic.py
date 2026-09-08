from elastic.configuration import get_elasticsearch_client
from generator.embeddings import serialize_record


def vector_matching(records, model, dataset_id, k_value, num_candidates):

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
            "k": k_value,
            "num_candidates": num_candidates
        },
    })
    return client.msearch(body=body)




