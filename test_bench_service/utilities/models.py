from jinja2.nodes import List
from pydantic.v1 import BaseModel

class BaseDataNames(BaseModel):
    first_name: str
    last_name: str
    full_names: list[str]

class BaseDataAddresses(BaseModel):
    address_lines: list[str]
    postal_code: str
    country: str

class BaseDataRecord(BaseModel):
    id: str
    dataset_id: str
    names: BaseDataNames
    addresses: BaseDataAddresses
    phone_number: str
    longitude: float
    latitude: float
    lsh_buckets: list[str]

class SkewedDataRecord(BaseModel):
    id: str
    dataset_id: str
    base_data_id: str
    names: BaseDataNames
    addresses: BaseDataAddresses
    phone_number: str
    longitude: float
    latitude: float
    lsh_buckets: list[str]
    graph : list[float]