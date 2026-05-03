import uuid
from fastapi import HTTPException

import psycopg
from elasticsearch import helpers
from datetime import datetime, timezone
from utilities.main import database_cursor, database_connection
from data_gen.elastic.configuration import get_elasticsearch_client
from utilities.models import ConfusionMatrix


def create_schema():
    with database_connection() as connection:
        with database_cursor(connection) as cursor:

            cursor.execute('''
            
                CREATE EXTENSION IF NOT EXISTS postgis;

                CREATE TABLE IF NOT EXISTS dataset (
                    id varchar CONSTRAINT primary_key_dataset PRIMARY KEY,
                    name varchar UNIQUE,
                    base_data_last_updated timestamp,
                    base_data_count integer,
                    skewed_data_last_updated timestamp,
                    skewed_data_count integer,
                    created_on timestamp
                );

                CREATE TABLE IF NOT EXISTS base_data (
                    id varchar CONSTRAINT primary_key_base_data PRIMARY KEY,
                    dataset_id varchar,
                    first_name varchar,
                    last_name varchar,
                    location geography(Point, 4326),
                    CONSTRAINT fk_base_dataset
                        FOREIGN KEY (dataset_id)
                        REFERENCES dataset(id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS skewed_data (
                    id varchar CONSTRAINT primary_key_skewed_data PRIMARY KEY,
                    dataset_id varchar,
                    base_data_id varchar,
                    first_name varchar,
                    last_name varchar,
                    location geography(Point, 4326),

                    CONSTRAINT fk_skewed_dataset
                        FOREIGN KEY (dataset_id)
                        REFERENCES dataset(id)
                        ON DELETE CASCADE,

                    CONSTRAINT fk_skewed_base_data
                        FOREIGN KEY (base_data_id)
                        REFERENCES base_data(id)
                        ON DELETE CASCADE
                );
                    
                CREATE TABLE IF NOT EXISTS run_history(
                    id varchar CONSTRAINT primary_key_run_history PRIMARY KEY,
                    dataset_id varchar,
                    timestamp timestamp,
                    technique varchar,
                    total_records integer,
                    true_positives integer,
                    false_positives integer,
                    true_negatives integer,
                    false_negatives integer,
                    
                    CONSTRAINT fk_run_history_dataset
                        FOREIGN KEY (dataset_id)
                        REFERENCES dataset(id)
                        ON DELETE CASCADE
                );
                    
                CREATE TABLE IF NOT EXISTS run_history_hits(
                    id varchar CONSTRAINT primary_key_run_history_hit PRIMARY KEY,
                    run_history_id varchar,
                    base_data_id varchar,
                    true_hit boolean,
                    
                    CONSTRAINT fk_run_history_base_data
                        FOREIGN KEY (base_data_id)
                        REFERENCES base_data(id)
                        ON DELETE CASCADE
                )
            ''')
            connection.commit()
            cursor.close()
            connection.close()

def generate_dataset(dataset_name: str):
    with database_connection() as connection:
        with database_cursor(connection) as cursor:

            elastic = get_elasticsearch_client()

            dataset_id = uuid.uuid4()

            try:
                cursor.execute(
                    "INSERT INTO dataset (id, name, base_data_last_updated, base_data_count, skewed_data_last_updated, skewed_data_count, created_on) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    [str(dataset_id), dataset_name, None, None,
                     None, None, datetime.now(timezone.utc)]
                )
                connection.commit()
                cursor.close()
                connection.close()
                return dataset_id
            except psycopg.errors.UniqueViolation:
                connection.rollback()
                raise HTTPException(
                    status_code=409,
                    detail={'error_code': 'UNIQUE_VIOLATION'}
                )

def load_base_records(records: list[list[str]], dataset_id: str):
    with database_connection() as connection:
        with database_cursor(connection) as cursor:

            elastic = get_elasticsearch_client()

            cursor.executemany(
                """
                INSERT INTO base_data (id, first_name, last_name, location, dataset_id)
                VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s,%s), 4326), %s)
                """,
                [(r[0], r[1], r[2], r[3], r[4], str(dataset_id)) for r in records[1:]]
            )

            cursor.execute('''
                           UPDATE dataset
                           SET base_data_last_updated = %s,
                               base_data_count        = %s
                           WHERE id = %s
                           ''', (datetime.now(timezone.utc), len(records) - 1, str(dataset_id)))

            if elastic.indices.exists(index=dataset_id):
                elastic.indices.delete(
                    index=dataset_id,
                )

            elastic.indices.create(
                index=dataset_id,
                body={
                    'mappings': {
                        'properties': {
                            'id': {'type': 'keyword'},
                            'first_name': {'type': 'text'},
                            'last_name': {'type': 'text'},
                            'location': {'type': 'geo_point'},
                        }
                    }
                }
            )

            elastic_records = []

            for row in records[1:]:
                elastic_records.append({
                    '_index': dataset_id,
                    '_id': row[0],
                    '_source': {
                        'id': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'location': f'POINT (${row[3]} ${row[4]})',
                    }
                })

            helpers.bulk(elastic,elastic_records)

            connection.commit()
            cursor.close()
            connection.close()
            return dataset_id

def load_skewed_records(skewed_records: list[list[str]], dataset_id):
    with database_connection() as connection:
        with database_cursor(connection) as cursor:
            cursor.executemany(
                "INSERT INTO skewed_data (id, first_name, last_name, location, base_data_id, dataset_id) VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)",
                [(r[0], r[1], r[2], r[3], r[4], r[5], str(dataset_id)) for r in skewed_records[1:]]
            )
            cursor.execute('''
                           UPDATE dataset
                           SET skewed_data_last_updated = %s,
                               skewed_data_count        = %s
                           WHERE id = %s
                           ''', (datetime.now(timezone.utc), len(skewed_records) - 1, str(dataset_id)))
            connection.commit()
            cursor.close()
            connection.close()

def create_run_history(dataset_id: str, results: ConfusionMatrix, technique: str, true_hits: list[str], false_hits: list[str]):
    with database_connection() as connection:
        with database_cursor(connection) as cursor:
            run_history_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO run_history (id, dataset_id, timestamp, technique, total_records, true_positives, false_positives, true_negatives, false_negatives) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''',(run_history_id, dataset_id, datetime.now(timezone.utc), technique,results.total_records,results.true_positives, results.false_positives, results.true_negatives, results.false_negatives))
            query = "INSERT INTO run_history_hits (id, run_history_id, base_data_id, true_hit) values (%s, %s, %s, %s)"
            for hit in true_hits:
                cursor.execute(query, (str(uuid.uuid4()), run_history_id, hit, True))
            for hit in false_hits:
                cursor.execute(query, (str(uuid.uuid4()), run_history_id, hit, False))
            connection.commit()
            cursor.close()
            connection.close()

def create_run_history_hit(run_history_id: str,base_data_id: str, is_true_hit: bool):
    pass
