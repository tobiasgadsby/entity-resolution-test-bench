from scipy._lib.cobyqa import settings

from elastic.configuration import get_elasticsearch_client
from generator.hashing import generate_shingles, preprocessing, generate_minhash_signature, generate_lsh_buckets
from test_bench_service.utilities.models import SkewedDataRecord


def bucket_matches(skewed_records: SkewedDataRecord, dataset_id):

    body = []

    client = get_elasticsearch_client()

    for record in skewed_records:

        processed_record = preprocessing(record)
        shingles = generate_shingles(processed_record, 6)
        print(f"QUERYING AS: [{processed_record}]")

        minhash = generate_minhash_signature(shingles)
        buckets = generate_lsh_buckets(minhash)
        print(f'query bucket 0: {buckets[0]}')

        body.append({'index': dataset_id})
        body.append({
            "size": 100,
            "query": {
                "terms": {
                    "lsh_buckets": buckets
                }
            }
        })
    return client.msearch(body=body)