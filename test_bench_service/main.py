import csv
import subprocess
from contextlib import asynccontextmanager
from io import TextIOWrapper
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.params import Query, Form, File
from generator.main import generate_base_records, generate_skewed_data, load_base_records_from_file
from loader.main import generate_dataset, load_base_records, load_skewed_records, create_schema, create_run_history
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from utilities.main import database_cursor, database_connection, delete_dataset, dict_database_cursor

from test_bench_service.techniques.levenstein import elasticsearch_levenstein_matching

from data_gen.elastic.configuration import get_elasticsearch_client
from utilities.models import ConfusionMatrix


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_schema()
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    'http://localhost:5173'
]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
@app.post('/data-gen/generate/dataset/{name}')
async def data_gen(name: str, count: int, skewed_techniques: list[str] = Query(default=[]), base_data_file: Optional[UploadFile] = File(None), skewed_data_file: Optional[UploadFile] = File(None)):
    print("generating dataset and base data : ", name)
    if len(skewed_techniques) == 0:
        raise HTTPException(
            status_code=409,
            detail={'error_code': 'SKEWED_TECHNIQUES_EMPTY'}
        )

    if base_data_file is not None:
        print("Loading base data from file")
        base_data_file = list(csv.reader(TextIOWrapper(base_data_file.file, encoding='utf-8')))
        base_data = load_base_records_from_file(base_data_file)
    else:
        print("generating base data")
        base_data = generate_base_records(count)
    dataset_id = generate_dataset(name)
    load_base_records(base_data, dataset_id)

    if skewed_data_file is not None:
        print("Loading skewed data from file")
        skewed_data_file = list(csv.reader(TextIOWrapper(skewed_data_file.file, encoding='utf-8')))
        skewed_data = load_base_records_from_file(skewed_data_file)
    else:
        print("generating skewed data")
        skewed_data = generate_skewed_data(dataset_id, records=base_data[1:], skewed_techniques=skewed_techniques)
    load_skewed_records(skewed_data, dataset_id)
    return {"status": "success"}

@app.delete('/data-gen/datasets/{dataset_id}')
async def dataset_delete(dataset_id: str):
    delete_dataset(dataset_id)

@app.post('/techniques/levenstein')
async def levenstein_matching(dataset_id: str):
    print("levenstein matching")
    with database_connection() as connection:
        with database_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM skewed_data WHERE dataset_id = %s", (dataset_id,))
            records = cursor.fetchall()
            print("records: ", records)
            result = elasticsearch_levenstein_matching(records, get_elasticsearch_client(), dataset_id)
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
                print('record: ',record)
                expected_id = record[2]
                hits = res['hits']['hits']

                returned_ids = [hit['_source']['id'] for hit in hits]

                print('expected: ',expected_id)
                print('returned: ',returned_ids)

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

            create_run_history(dataset_id, confusion_matrix, 'levenshtein', true_hits, false_hits)

@app.get('/data-gen/datasets')
async def get_datasets():
    with database_connection() as connection:
        with database_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM dataset")
            records = cursor.fetchall()
            print(records)
            return [{
                "dataset_id": record[0],
                "dataset_name": record[1],
                "base_data_last_updated": record[2],
                "base_data_count": record[3],
                "skewed_data_last_updated": record[4],
                "skewed_data_count": record[5],
                "created_on": record[6]
            } for record in records]

@app.get('/run-history/{dataset_id}')
async def get_run_history(dataset_id: str):
    with database_connection() as connection:
        with database_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM run_history WHERE dataset_id = %s", (dataset_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return [{
                "run_id": record[0],
                "dataset_id": record[1],
                "timestamp": record[2],
                "technique": record[3],
                "total_records": record[4],
                "true_positives": record[5],
                "false_positives": record[6],
                "true_negatives": record[7],
                "false_negatives": record[8]
            } for record in records]

@app.get('/run-history/{run_history_id}/hits')
async def get_run_history_hits(run_history_id: str):
    with database_connection() as connection:
        with dict_database_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM run_history_hits INNER JOIN base_data ON run_history_hits.base_data_id = base_data.id WHERE run_history_id = %s ", (run_history_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records

@app.get('/datasets/{dataset_id}/base_data')
async def get_base_data(dataset_id: str):
    with database_connection() as connection:
        with dict_database_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM base_data WHERE dataset_id = %s", (dataset_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records

@app.get('/datasets/{dataset_id}/skewed_data')
async def get_base_data(dataset_id: str):
    with database_connection() as connection:
        with dict_database_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM skewed_data WHERE dataset_id = %s", (dataset_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records