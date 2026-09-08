import time
from typing import List

from test_bench_service.utilities.models import BaseDataRecord

def serialize_record(record: BaseDataRecord):
    parts = []

    if record.names.first_name: parts.append(f"First Name: {record.names.first_name.strip()}")
    if record.names.last_name: parts.append(f"Last Name: {record.names.last_name.strip()}")
    if record.names.full_names: parts.append(f"Full Names: {', '.join(record.names.full_names)}")
    if record.phone_number: parts.append(f"Phone Number: {record.phone_number.strip()}")
    if record.addresses.address_lines: parts.append(f"Address Lines: {', '.join(record.addresses.address_lines)}")
    if record.addresses.postal_code: parts.append(f"Postal Code: {', '.join(record.addresses.postal_code)}")
    if record.addresses.country: parts.append(f"Country: {', '.join(record.addresses.country)}")

    serialised_text = ". ".join(parts) + "."
    return serialised_text

def generate_semantic_embeddings(records: List[BaseDataRecord], model):
    records_to_embed = [serialize_record(record) for record in records]

    print(f"Generating embeddings for {len(records_to_embed)} records")
    start_time = time.time()

    embeddings = model.encode(records_to_embed, convert_to_tensor=True, show_progress_bar=True)

    end_time = time.time()
    print(f"Elapsed time: {end_time - start_time} seconds")

    return embeddings

