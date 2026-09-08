import hashlib
from typing import List

from datasketch import MinHash, MinHashLSH

from test_bench_service.utilities.models import BaseDataRecord
import re


def preprocessing(record: BaseDataRecord) -> str:
    parts =[]

    if record.names:
        if record.names.first_name:
            parts.append(record.names.first_name)
        if record.names.last_name:
            parts.append(record.names.last_name)
        if record.names.full_names:
            parts.extend(record.names.full_names)

    if record.addresses:
        if record.addresses.address_lines:
            parts.extend(record.addresses.address_lines)
        if record.addresses.postal_code:
            parts.append(record.addresses.postal_code)
        if record.addresses.country:
            parts.append(record.addresses.country)

    if record.phone_number:
        parts.append(record.phone_number)

    if record.longitude is not None:
        parts.append(str(record.longitude))
    if record.latitude is not None:
        parts.append(str(record.latitude))

    full_text = " ".join(parts)

    return re.sub(r'[^a-z0-9 ]', '', full_text.lower()).strip()


def generate_shingles(field: str, k: int):

    shingles = set()

    for i in range(len(field) - k + 1):
        shingles.add(field[i:i + k])

    return shingles

def generate_minhash_signature(shingle_set):

    m_hash = MinHash(num_perm=128, seed=42)

    for shingle in shingle_set:
        m_hash.update(shingle.encode('utf-8'))

    return m_hash

def generate_lsh_buckets(minhash, num_bands=2, rows_per_band=64):

    hashes = minhash.hashvalues

    buckets = []

    for i in range(num_bands):
        start = i * rows_per_band
        end = start + rows_per_band

        band = hashes[start:end]

        band_bytes = band.tobytes()

        band_hash = hashlib.md5(band_bytes).hexdigest()

        key = f'b{i}_{band_hash}'
        buckets.append(key)
    return buckets

def build_index(base_data: List[BaseDataRecord]):

    for record in base_data:

        processed_record = preprocessing(record)

        print(f"INDEXING AS: [{processed_record}]")

        shingle_set = generate_shingles(processed_record, 6)

        signature  = generate_minhash_signature(shingle_set)

        record.lsh_buckets = generate_lsh_buckets(minhash=signature)

    return base_data