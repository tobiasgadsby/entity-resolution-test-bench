from dotenv import load_dotenv
import psycopg
import os

from psycopg.rows import dict_row

from elastic.configuration import get_elasticsearch_client


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
                                id,
                                dataset_id,
                                first_name,
                                last_name,
                                ST_Y(location::geometry) AS lat,
                                ST_X(location::geometry) AS lon
                            FROM {source}
                            WHERE dataset_id = %s;
                           ''', (dataset_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records