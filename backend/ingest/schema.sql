with psycopg.connect(DATABASE_URL) as conn:
    conn.execute(open("ingest/schema.sql").read())
