import csv
import random
import uuid
from io import StringIO

from faker import Faker
from fastapi import UploadFile

from skews.main import swap_chars, location_drift
from utilities.main import database_connection, database_cursor


def generate_base_records(count: int) -> list[list[str]]:
    fake = Faker()
    records = [['ID','FIRST_NAME','LAST_NAME', 'LONGITUDE', 'LATITUDE']]
    for i in range(count):
        records.append([
            str(uuid.uuid4()),
            fake.first_name(),
            fake.last_name(),
            random.uniform(-180, 180),
            random.uniform(-90, 90),
        ])
    return records

def load_base_records_from_file(base_data_file: list[list[str]]) -> list[list[str]]:
    records = [['ID','FIRST_NAME','LAST_NAME','LONGITUDE','LATITUDE']]
    for row in base_data_file:
        records.append([
            str(uuid.uuid4()),
            row[0],
            row[1],
            row[2],
            row[3]
        ])
    return records

def generate_skewed_data(dataset_id, records, skewed_techniques):
    skewed_records = [['ID', 'FIRST_NAME', 'LAST_NAME', 'LONGITUDE', 'LATITUDE', 'BASE_DATA_ID']]

    for record in records:
        for technique in skewed_techniques:
            match technique:
                case 'SWAP_CHAR':
                    skewed_records.append([str(uuid.uuid4()), swap_chars(record[1], 1, 2), swap_chars(record[2], 1, 2), record[3], record[4] ,record[0]])
                case 'REMOVE_FIELD':
                    skewed_record = record
                    skewed_record[1] = ""
                    skewed_record.append(record[0])
                    skewed_records.append(skewed_record)
                case 'LOCATION_DRIFT':
                    skewed_record = record
                    skewed_record[3], skewed_record[4] = location_drift(skewed_record[3], skewed_record[4], 0.2)
                    skewed_record.append(record[0])
                    skewed_records.append(skewed_record)
    print("Skewed record count: ",len(skewed_records))
    return skewed_records