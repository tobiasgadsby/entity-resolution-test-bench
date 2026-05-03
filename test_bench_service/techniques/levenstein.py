import os

def elasticsearch_levenstein_matching(records, client, dataset_id):

    body = []
    print(dataset_id)
    print(records[0])

    for record in records:
        body.append({"index": dataset_id})
        body.append({
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "first_name": {
                                    "query": record[3],
                                    "fuzziness": 1
                                }
                            }
                        },
                        {
                            "match": {
                                "last_name": {
                                    "query": record[4],
                                    "fuzziness": 1
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 2
                }
            }
        })

    return client.msearch(body=body)