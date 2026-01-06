import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import os
from urllib.parse import quote_plus
from urllib.parse import unquote_plus

def execute_and_print_query(sql_query):
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST","postgres.cs.rutgers.edu")
    DB_PORT = os.getenv("DB_PORT","5432")
    DB_NAME = os.getenv("DB_NAME")

    if not all([DB_USER, DB_PASSWORD, DB_NAME]):
        raise ValueError("Missing one or more required environment variables: DB_USER, DB_PASSWORD, DB_NAME")

    #encoded_password = quote_plus(DB_PASSWORD)


    #db_url = (
    #        f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    #)

    real_password = unquote_plus(DB_PASSWORD)
    safe_password = real_password.replace('@', '%40').replace('#', '%23')
    db_url = f"postgresql+psycopg2://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    #db_url = URL.create(
    #        drivername="postgressql+psycopg2",
    #        username = DB_USER,
    #        password = DB_PASSWORD,
    #        host = DB_HOST,
    #        port = int(DB_PORT),
    #        database = DB_NAME
    #)

    try:
        engine = create_engine(db_url)

        with engine.connect() as connection:
            connection.execute(text("SET search_path TO public;"))
            #connection.commit()
            df = pd.read_sql_query(text(sql_query), connection)

        #df = pd.read_sql_query(sql_query, engine)
        if df is None or df.empty:
            print(f"Query executed successfully, but returned 0 rows: {sql_query}")

            table_check = pd.read_sql_query(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"),
                    engine
            )
            print(f"Query returned 0 rows. Available tables in public: {table_check['table_name'].tolist()}")
            return

        print(df.to_string(index=False))

    except Exception as e:
        print(f"--- DATABASE ERROR ---")
        print(f"Failed to execute query: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No SQL query provided.") #added
        sys.exit(1) #added

    full_sql_from_cmd = " ".join(sys.argv[1:]).strip()

    if full_sql_from_cmd:
        execute_and_print_query(full_sql_from_cmd)
        #if sys.stdin.isatty():
        #     print("Usage: python3 ilab_script.py \"SELECT * FROM table;\"")
        #     sys.exit(1)
        #sql_query = sys.stdin.read().strip()
        #if not sql_query:
        #    print("Error: No SQL query received via STDIN.")
        #    sys.exit(1)
    #else:
    #    sql_query = sys.argv[1].strip()

    #if sql_query:
    #    execute_and_print_query(sql_query)