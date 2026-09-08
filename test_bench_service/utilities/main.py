from typing import List

from test_bench_service.utilities.models import BaseDataRecord, SkewedDataRecord
from utilities.models import ConfusionMatrix


def calculate_confusion_matrix(records: List[SkewedDataRecord], result):
    confusion_matrix = ConfusionMatrix(
        total_records=len(records),
        true_positives=0,
        false_positives=0,
        true_negatives=0,
        false_negatives=0
    )
    true_hits = []
    false_hits = []
    for record, res in zip(records, result['responses']):
        expected_id = record.base_data_id
        print(res)
        hits = res['hits']['hits']

        returned_ids = [hit['_source']['id'] for hit in hits]

        if expected_id in returned_ids:
            confusion_matrix.true_positives += 1

            confusion_matrix.false_positives += sum(
                1 for _id in returned_ids if _id != expected_id
            )

            confusion_matrix.true_negatives += len(records) - len(returned_ids)

            true_hits.append(expected_id)

            false_hits.extend([_i for _i in returned_ids if _i != expected_id])
        else:
            confusion_matrix.false_negatives += 1
            confusion_matrix.true_negatives += len(records) - len(returned_ids) - 1
            confusion_matrix.false_positives += len(returned_ids)
            false_hits.extend(returned_ids)
    print(f'Confusion Matrix:\n{confusion_matrix}')
    return confusion_matrix, true_hits, false_hits