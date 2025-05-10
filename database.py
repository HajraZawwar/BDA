from pymongo import MongoClient
# from cassandra.cluster import Cluster
from neo4j import GraphDatabase
import boto3
import faiss
import numpy as np
import config


# MongoDB
mongo_client = MongoClient(config.MONGO_URI)
mongo_db = mongo_client["instagram_lite"]

# Cassandra
# cassandra_cluster = Cluster(config.CASSANDRA_HOSTS)
# cassandra_session = cassandra_cluster.connect()
# cassandra_session.set_keyspace(config.CASSANDRA_KEYSPACE)

# Neo4j
neo4j_driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

# DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=config.DYNAMODB_REGION,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
)

session_table = dynamodb.Table(config.DYNAMODB_SESSION_TABLE)

# S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
)

# FAISS (Load empty or existing index)
try:
    faiss_index = faiss.read_index(config.FAISS_INDEX_PATH)
except:
    faiss_index = faiss.IndexFlatL2(128)  # Use 128-dim vectors by default
