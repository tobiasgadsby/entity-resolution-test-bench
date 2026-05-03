import os
from elasticsearch import Elasticsearch

def get_elasticsearch_client() -> Elasticsearch:
    return Elasticsearch(
        os.environ['ELASTICSEARCH_URL'],
        api_key=os.environ['ELASTICSEARCH_API_KEY'],
    )