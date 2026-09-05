import psychopg2

hostname = 'localhost'
database = 'anti-poaching-system'
username = 'postgres'
pwd = '1738'
port_id = 5432

conn = psychopg2.connect(
    host=hostname,
    database=database,
    user=username,
    password=pwd,
    port=port_id
)

conn.close()
