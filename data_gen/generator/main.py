import random
import uuid
from typing import List

from faker import Faker

from skews.main import swap_chars, location_drift
from test_bench_service.utilities.models import BaseDataRecord, SkewedDataRecord, BaseDataNames, BaseDataAddresses


def generate_fake_address(fake) -> BaseDataAddresses:
    raw_address = fake.address()
    lines = raw_address.split('\n')

    return BaseDataAddresses(
        address_lines=lines,
        postal_code=fake.postcode(),
        country=fake.country()
    )


def generate_base_records(count: int) -> List[BaseDataRecord]:
    fake = Faker()
    records = []
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        records.append(BaseDataRecord(
            id=str(uuid.uuid4()),
            dataset_id='',
            names=BaseDataNames(
                first_name=first_name,
                last_name=last_name,
                full_names=[f'{first_name} {last_name}']
            ),
            addresses=generate_fake_address(fake),
            phone_number=fake.phone_number(),
            longitude=random.randint(-180, 180),
            latitude=random.randint(-90, 90),
            lsh_buckets=[]
        ))
    return records


def load_base_records_from_file(base_data_file: list[list[str]], is_sanctions: bool = True) -> list[BaseDataRecord]:
    base_data_file = base_data_file[2:]
    if is_sanctions:
        return process_sanctions_file(base_data_file)


def process_sanctions_file(base_data_file: list[list[str]]):
    return [
        BaseDataRecord(
            id=str(uuid.uuid4()),
            dataset_id='',
            names=BaseDataNames(
                first_name='',
                last_name='',
                full_names=[name for name in [record[4], record[5], record[6]] if name.strip()]
            ),
            addresses=BaseDataAddresses(
                address_lines=[addr for addr in [record[22], record[23], record[24]] if addr.strip()],
                postal_code=record[28].strip(),
                country=record[29].strip()
            ),
            phone_number=record[30].strip(),
            longitude=0,
            latitude=0,
            lsh_buckets=[]
        )
        for record in base_data_file]


def generate_skewed_data(dataset_id, records: List[BaseDataRecord], skewed_techniques) -> List[SkewedDataRecord]:
    skewed_records = []

    for record in records:
        for technique in skewed_techniques:
            match technique:
                case 'SWAP_CHAR':
                    skewed_record = SkewedDataRecord(**record.dict(), base_data_id=record.id, graph=[])
                    skewed_record.id = str(uuid.uuid4())
                    skewed_record.names.first_name = swap_chars(skewed_record.names.first_name, random.randint(0,5)) if skewed_record.names.first_name != '' else ''
                    skewed_record.names.last_name = swap_chars(skewed_record.names.last_name, random.randint(0, 5)) if skewed_record.names.last_name != '' else ''
                    skewed_record.names.full_names = [swap_chars(name, random.randint(0, 5)) if name != '' else ''for name in skewed_record.names.full_names]
                    skewed_record.addresses.address_lines = [swap_chars(line, random.randint(0, 5)) if line != '' else ''for line in skewed_record.addresses.address_lines]
                    skewed_record.addresses.postal_code = swap_chars(skewed_record.addresses.postal_code,random.randint(0,5)) if skewed_record.addresses.postal_code != '' else ''
                    skewed_record.addresses.country = swap_chars(skewed_record.addresses.country, random.randint(0,5)) if skewed_record.addresses.country != '' else ''
                    skewed_record.phone_number = swap_chars(skewed_record.phone_number, random.randint(0, 5)) if skewed_record.phone_number != '' else ''
                    skewed_records.append(skewed_record)
                case 'REMOVE_FIELD':
                    skewed_record = SkewedDataRecord(**record.dict(), base_data_id=record.id)
                    skewed_record.first_name = ""
                    skewed_record.id = str(uuid.uuid4())
                    skewed_record.base_data_id = record.id
                    skewed_records.append(skewed_record)
                case 'LOCATION_DRIFT':
                    skewed_record = SkewedDataRecord(**record.dict(), base_data_id=record.id)
                    skewed_record.id = str(uuid.uuid4())
                    skewed_record.longitude, skewed_record.latitude = location_drift(record.longitude, record.latitude,0.2)
                    skewed_record.base_data_id = record.id
                    skewed_records.append(skewed_record)
    print("Skewed record count: ", len(skewed_records))
    return skewed_records
