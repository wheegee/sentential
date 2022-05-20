import boto3
import psycopg
import tempfile

from config.env import AWS_REGION
from config.ssm import rds_config

session = boto3.Session(region_name=AWS_REGION)
client = session.client('rds')

def rds_endpoint():
    instances = client.describe_db_instances(DBInstanceIdentifier=rds_config.db_instance)['DBInstances']
    for instance in instances:
        if rds_config.db_instance == instance['DBInstanceIdentifier']:
            endpoint = instance['Endpoint']['Address']
            port = instance['Endpoint']['Port']
            return endpoint, port

def rds_token(endpoint, port):
    return client.generate_db_auth_token(DBHostname=endpoint, Port=port, DBUsername=rds_config.db_user, Region=AWS_REGION)

def rds_client():
    with tempfile.NamedTemporaryFile() as root_cert:
        root_cert.write(bytes(rds_config.db_root_cert, 'utf-8'))
        root_cert.seek(0)
        endpoint, port = rds_endpoint()
        return psycopg.connect(
            host=endpoint,
            port=port,
            user=rds_config.db_user,
            password=rds_token(endpoint, port),
            sslrootcert=root_cert.name,
            sslmode="verify-full",
            dbname=rds_config.db_name)

