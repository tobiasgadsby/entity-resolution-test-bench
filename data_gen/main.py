import sqlite3

from generator.main import generate_base_records, generate_skewed_data
from loader.main import load_records

def generate_and_load_records(count, name):
    records = generate_base_records(count)
    load_records(records, generate_skewed_data(records), name)