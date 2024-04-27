import psycopg2
from tqdm import tqdm
import psycopg2
from psycopg2 import extensions, OperationalError

def execute_sql_line_by_line(filename, dbname, user, password, host='localhost', port='5432'):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    conn.autocommit = True
    cursor = conn.cursor()

    with open(filename, 'r', encoding='utf-8') as file:
        line_number = 0
        for line in tqdm(file):
            line_number += 1
            if line.strip():  # Skip empty lines
                try:
                    cursor.execute(line)

                except psycopg2.Error as e:
                    print(f"Error on line {line_number}: {e.pgerror}")
                    # Reset connection
                    conn = reset_connection(conn, dbname, user, password, host, port)
                    cursor = conn.cursor()

    cursor.close()
    conn.close()

def reset_connection(conn, dbname, user, password, host, port):
    if conn:
        conn.close()
    return psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)

# Example usage
if __name__ == "__main__":
    database_name = 'osm_database'
    username = 'postgres'
    password = '9417941'
    file_path = r"C:\Program Files\PostgreSQL\16\bin\landuse.sql"

    execute_sql_line_by_line(file_path, database_name, username, password)
