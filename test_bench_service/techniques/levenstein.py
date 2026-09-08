import os
from typing import List

from test_bench_service.utilities.models import BaseDataRecord


import os
from typing import List

from test_bench_service.utilities.models import BaseDataRecord


def elasticsearch_levenstein_matching(records: List[BaseDataRecord], client, dataset_id, levenshtein_fuzziness: int, levenshtein_min_should_match: int):

    body =[]

    for record in records:
        should_clauses =[]

        if record.names.first_name:
            should_clauses.append({
                "match": {
                    "first_name": {
                        "query": record.names.first_name,
                        "fuzziness": levenshtein_fuzziness
                    }
                }
            })

        if record.names.last_name:
            should_clauses.append({
                "match": {
                    "last_name": {
                        "query": record.names.last_name,
                        "fuzziness": levenshtein_fuzziness
                    }
                }
            })

        if record.names.full_names:
            for name in record.names.full_names:
                if name:
                    should_clauses.append({
                        "match": {
                            "full_names": {
                                "query": name,
                                "fuzziness": levenshtein_fuzziness
                            }
                        }
                    })

        if record.addresses.address_lines:
            for address_line in record.addresses.address_lines:
                if address_line:
                    should_clauses.append({
                        "match": {
                            "address_lines": {
                                "query": address_line,
                                "fuzziness": levenshtein_fuzziness
                            }
                        }
                    })

        if record.addresses.country:
            should_clauses.append({
                "match": {
                    "country": {
                        "query": record.addresses.country,
                        "fuzziness": levenshtein_fuzziness
                    }
                }
            })

        if record.addresses.postal_code:
            should_clauses.append({
                "match": {
                    "postal_code": {
                        "query": record.addresses.postal_code,
                        "fuzziness": levenshtein_fuzziness
                    }
                }
            })

        body.append({"index": dataset_id})
        body.append({
            "size": 100,
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": min(int(levenshtein_min_should_match), len(should_clauses))
                }
            }
        })
    return client.msearch(body=body)