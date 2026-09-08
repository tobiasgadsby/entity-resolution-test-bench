import codecs
import csv
import subprocess
from contextlib import asynccontextmanager
from io import TextIOWrapper
from typing import Optional

import torch
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.params import Query, Form, File
from sentence_transformers import SentenceTransformer

from generator.graphing import generate_graph
from generator.main import generate_base_records, generate_skewed_data, load_base_records_from_file
from generator.embeddings import generate_semantic_embeddings
from loader.main import generate_dataset, load_base_records, load_skewed_records, create_schema, create_run_history
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from test_bench_service.techniques.geospatial import geospatial_distance_matching
from test_bench_service.techniques.graphing import gnn_vector_search
from test_bench_service.techniques.locality_sensitive_hashing import bucket_matches
from test_bench_service.techniques.semantic import vector_matching
from test_bench_service.utilities.main import calculate_confusion_matrix
from utilities.main import database_cursor, database_connection, delete_dataset, dict_database_cursor, fetch_all

from test_bench_service.techniques.levenstein import elasticsearch_levenstein_matching

from data_gen.elastic.configuration import get_elasticsearch_client
from utilities.models import ConfusionMatrix

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_name = 'BAAI/bge-base-en-v1.5'

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Starting up... Loding model {model_name} with {device}')

    model = SentenceTransformer(model_name, device='cuda')
    ml_models['bge_encoder'] = model
    print(f'Model Loaded')

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
        csv_reader = csv.reader(codecs.iterdecode(base_data_file.file, 'utf-8'))
        base_data = load_base_records_from_file(list(csv_reader))
    else:
        print("generating base data")
        base_data = generate_base_records(count)
    dataset_id = generate_dataset(name)

    if skewed_data_file is not None:
        print("Loading skewed data from file")
        skewed_data_file = list(csv.reader(TextIOWrapper(skewed_data_file.file, encoding='utf-8')))
        skewed_data = load_base_records_from_file(skewed_data_file)
    else:
        print("generating skewed data")
        skewed_data = generate_skewed_data(dataset_id, records=base_data, skewed_techniques=skewed_techniques)
    base_data_graph, skewed_data_graph = generate_graph(base_data, skewed_data)
    load_base_records(base_data, dataset_id, generate_semantic_embeddings(base_data, ml_models['bge_encoder']), base_data_graph)
    load_skewed_records(skewed_data, dataset_id, skewed_data_graph)
    return {"status": "success"}

@app.delete('/data-gen/datasets/{dataset_id}')
async def dataset_delete(dataset_id: str):
    delete_dataset(dataset_id)

@app.post('/techniques/geospatial')
async def geospatial_matching(dataset_id: str):
    print("geospatial matching")
    records = fetch_all(dataset_id, False)
    result = geospatial_distance_matching(records, dataset_id)
    confusion_matrix, true_hits, false_hits = calculate_confusion_matrix(records, result)
    create_run_history(dataset_id, confusion_matrix, 'geospatial', true_hits, false_hits)

@app.post('/techniques/levenshtein')
async def levenstein_matching(dataset_id: str, levenshtein_fuzziness: str = Query(..., alias='levenshteinFuzziness'), levenshtein_min_should_match: str = Query(..., alias='levenshteinMinShouldMatch')):
    print("levenstein matching")
    records = fetch_all(dataset_id, False)
    result = elasticsearch_levenstein_matching(records, get_elasticsearch_client(), dataset_id, int(levenshtein_fuzziness), int(levenshtein_min_should_match))
    confusion_matrix, true_hits, false_hits = calculate_confusion_matrix(records, result)
    create_run_history(dataset_id, confusion_matrix, 'levenshtein', true_hits, false_hits)

@app.post('/techniques/semantic')
async def semantic_matching(dataset_id: str, k_value: int, num_of_candidates: int = Query(..., alias='numOfCandidates')):
    print("semantic matching")
    records = fetch_all(dataset_id, False)
    result = vector_matching(records, ml_models['bge_encoder'], dataset_id, k_value, num_of_candidates)
    confusion_matrix, true_hits, false_hits = calculate_confusion_matrix(records, result)
    create_run_history(dataset_id, confusion_matrix, 'semantic', true_hits, false_hits)#

@app.post('/techniques/hashing')
async def locality_sensitive_hashing_matching(dataset_id: str):
    print("locality sensitive hashing matching")
    records = fetch_all(dataset_id, False)
    result = bucket_matches(records, dataset_id)
    confusion_matrix, true_hits, false_hits = calculate_confusion_matrix(records, result)
    create_run_history(dataset_id,confusion_matrix, 'locality_sensitive_hashing', true_hits, false_hits)

@app.post('/techniques/graphing')
async def graphing_matching(dataset_id: str):
    print("graphing matching")
    records = fetch_all(dataset_id, False)
    result = gnn_vector_search(records, dataset_id)
    confusion_matrix, true_hits, false_hits = calculate_confusion_matrix(records, result)
    create_run_history(dataset_id, confusion_matrix, 'graphing', true_hits, false_hits)

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
            cursor.execute("SELECT * FROM run_history_hits INNER JOIN base_data ON run_history_hits.base_data_id = base_data.id WHERE run_history_id = %s LIMIT 100", (run_history_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records

@app.get('/datasets/{dataset_id}/base_data')
async def get_base_data(dataset_id: str):
    with database_connection() as connection:
        with dict_database_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM base_data WHERE dataset_id = %s LIMIT 100", (dataset_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records

@app.get('/datasets/{dataset_id}/skewed_data')
async def get_base_data(dataset_id: str):
    with database_connection() as connection:
        with dict_database_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM skewed_data WHERE dataset_id = %s LIMIT 100", (dataset_id,))
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records