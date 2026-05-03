from pydantic import BaseModel


class ConfusionMatrix(BaseModel):
    total_records: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int