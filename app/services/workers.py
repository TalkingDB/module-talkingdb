
from talkingdb.models.graph.graph import GraphModel
from talkingdb.clients.sqlite import sqlite_conn


def init_database():
    with sqlite_conn() as conn:
        GraphModel.init_db(conn)
    print("Database initialized.")


def start_workers():
    init_database()
    print("Workers started.")
