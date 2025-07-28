import os
from dotenv import load_dotenv
import psycopg
from pymongo import MongoClient

load_dotenv()

# PostgreSQL Connection Details
db_name_pg = os.getenv('POSTGRES_DB')
db_user_pg = os.getenv('POSTGRES_USER')
db_password_pg = os.getenv('POSTGRES_PASSWORD')
db_host_pg = os.getenv('POSTGRES_HOST', 'localhost')
db_port_pg = os.getenv('POSTGRES_PORT', '5432')

conn_str_pg = f'dbname={db_name_pg} user={db_user_pg} password={db_password_pg} host={db_host_pg} port={db_port_pg}'

# MongoDB Connection Details
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = int(os.getenv('MONGO_PORT', '27017'))
mongo_db_name = os.getenv('MONGO_DB_NAME', 'news_db_backup')
mongo_collection_name = os.getenv('MONGO_COLLECTION_NAME', 'articles')

try:
    # PostgreSQL Count
    with psycopg.connect(conn_str_pg) as conn_pg:
        with conn_pg.cursor() as cur_pg:
            cur_pg.execute("SELECT COUNT(*) FROM articles;")
            pg_count = cur_pg.fetchone()[0]
            print(f"PostgreSQL Articles: {pg_count}")

    # MongoDB Count
    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]
    mongo_count = collection.count_documents({})
    print(f"MongoDB Articles: {mongo_count}")
    client.close()

except Exception as e:
    print(f"Database query failed: {e}") 