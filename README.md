# CM3203 Final Project

Entity Resolution test bench allowing for data generation and comparison of entity resolution techniques.

## Getting Started

### Dependencies

* Install all the packages listed in the requirements.txt file. You may also need to separately install the data_gen module located in this directory.
* You can use the docker compose file [here](local/docker-compose.yaml) to run the postgres and elastic instance.
* You can also follow the guide [here](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/installing-elasticsearch) to install elasticsearch.
* Mae sure to provide the enviornment variables for ELASTICSEARCH_API_KEY, ELASTICSEARCH_URL, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST and DATABASE_PORT
* Run npm install in the frontend directory to install dependencies.

### Executing program

* Run fastapi dev in the test_bench_service directory to start the fastAPI backend.
* Run npm dev in the frontend director to start the frontend service.