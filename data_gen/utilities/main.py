import json

from dotenv import load_dotenv
import psycopg
import os

from psycopg.rows import dict_row

from elastic.configuration import get_elasticsearch_client
from test_bench_service.utilities.models import BaseDataRecord, SkewedDataRecord, BaseDataNames, BaseDataAddresses


def database_cursor(connection):
    return connection.cursor()

def dict_database_cursor(connection):
    return connection.cursor(row_factory=dict_row)

def database_connection():
    load_dotenv()
    return psycopg.connect(f'dbname={os.getenv("DATABASE_NAME")} user={os.getenv("DATABASE_USER")} password={os.getenv("DATABASE_PASSWORD")} host={os.getenv("DATABASE_HOST")} port={os.getenv("DATABASE_PORT")}')

def delete_dataset(dataset_id):
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''
                DELETE FROM dataset
                WHERE id = %s
            ''', (dataset_id,))
            elastic = get_elasticsearch_client()
            elastic.indices.delete(index=dataset_id)
            connection.commit()
            cursor.close()
            connection.close()

def fetch_all(dataset_id, isBaseData: bool):
    with database_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            source = 'base_data' if isBaseData else 'skewed_data'
            cursor.execute(f'''
                           SELECT 
                                {'base_data_id,' if not isBaseData else ''}
                                id,
                                dataset_id,
                                first_name,
                                last_name,
                                full_names,
                                phone_number,
                                address_lines,
                                postal_code,
                                country,
                                ST_Y(location::geometry) AS lat,
                                ST_X(location::geometry) AS lon,
                                graph_vector
                            FROM {source}
                            WHERE dataset_id = %s;
                           ''', (dataset_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return [BaseDataRecord(
                id=record['id'],
                dataset_id=record['dataset_id'],
                names=BaseDataNames(
                    first_name=record['first_name'],
                    last_name=record['last_name'],
                    full_names=record['full_names']
                ),
                phone_number=record['phone_number'],
                addresses=BaseDataAddresses(
                    address_lines=record['address_lines'],
                    postal_code=record['postal_code'],
                    country=record['country']
                ),
                latitude=record['lat'],
                longitude=record['lon'],
            ) for record in records] if isBaseData else [SkewedDataRecord(
                id=record['id'],
                dataset_id=record['dataset_id'],
                base_data_id=record['base_data_id'],
                names=BaseDataNames(
                    first_name=record['first_name'],
                    last_name=record['last_name'],
                    full_names=record['full_names']
                ),
                phone_number=record['phone_number'],
                addresses=BaseDataAddresses(
                    address_lines=record['address_lines'],
                    postal_code=record['postal_code'],
                    country=record['country']
                ),
                latitude=record['lat'],
                longitude=record['lon'],
                lsh_buckets=[],
                graph=json.loads(record['graph_vector'])
            ) for record in records]

def extract_bigrams(field: str):

    field = field.lower().replace(' ', '')
    return [field[i:i+2] for i in range(len(field)-1)] if len(field) > 1 else [field]