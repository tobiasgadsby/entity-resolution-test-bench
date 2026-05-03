from elastic.configuration import get_elasticsearch_client


def geospatial_distance_matching(records, dataset_id):
    body = []

    client = get_elasticsearch_client()

    for record in records:
        body.append({"index": dataset_id})
        body.append({
            "query": {
                "bool": {
                    "filter": {
                        "geo_distance": {
                            "distance": "10km",
                            "location": {
                                "lon": record['lon'],
                                "lat": record['lat']
                            }
                        }
                    }
                }
            }
        })
    return client.msearch(body=body)