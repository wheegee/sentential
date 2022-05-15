import boto3
import psycopg
import tempfile

from config.env import AWS_REGION
from config.ssm import rds_config

session = boto3.Session(region_name=AWS_REGION)
client = session.client('rds')

instances = client.describe_db_instances(DBInstanceIdentifier=rds_config.instance)['DBInstances']
endpoint = None
port = None
for instance in instances:
    if rds_config.instance == instance['DBInstanceIdentifier']:
        endpoint = instance['Endpoint']['Address']
        port = instance['Endpoint']['Port']

token = client.generate_db_auth_token(DBHostname=endpoint, Port=port, DBUsername=rds_config.user, Region=AWS_REGION)

db_conn = None
try:
    with tempfile.NamedTemporaryFile() as root_cert:
        root_cert.write(bytes(rds_config.root_cert, 'utf-8'))
        root_cert.seek(0)
        db_conn = psycopg.connect(
            host=endpoint,
            port=port,
            user=rds_config.user,
            password=token,
            sslrootcert=root_cert.name,
            sslmode="verify-full",
            dbname=rds_config.database)
except Exception as e:
    print("Database connection failed due to {}".format(e))
