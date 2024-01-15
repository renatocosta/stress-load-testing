import json
import os
from faker import Faker
import random
from common.database import database
import sys

MAX_USERS = 500000
#todo refac
CONSUMERS_PASSWORDS = {
    'gerosa': '1234',
    'renan.txt': '1234',
    'mateus.homolog': '123456',
    'vagner': '1234'
}

def get_consumer_credit_card_id():
    if 'PAYMENT_METHODS' not in os.environ:
        raise ValueError('PaymentMethods not set')

    consumer_data = json.loads(os.environ['PAYMENT_METHODS'])

    consumer_credit_card = 0
    if len(consumer_data['data']['PaymentMethods']) > 0:
        # Pega o primeiro cartao de credito cadastrado
        consumer_credit_card = consumer_data['data']['PaymentMethods'][0]['id']

    return consumer_credit_card

def prepare_headers():
    fake = Faker('pt_BR')

    device_os = ['android', 'ios']
    app_version = ['10.19.29', '10.19.29']
    device_id = os.environ['testing_LOADTEST_PREFIX'] + fake.uuid4()
    device_id = device_id[:36]

    headers = {
        'content-type': 'application/json',
        'Accept-Encoding':'gzip',
        'android_id':'122fe7218a394d05',
        'app_version': random.choice(app_version),
        'device_id': device_id,
        'device_model':'samsungSM-G532MT',
        'device_os': random.choice(device_os),
        'installation_id': device_id,
        'ip': fake.ipv4_public(network=False, address_class=None)
    }

    return headers

def save_consumer_load_test_credentials(email, name, password):
    conn = database()
    sql_query = 'INSERT INTO consumers (id, email, name, password) VALUES (NULL, "%s","%s", "%s");' % (email, name, password)
    conn.query(sql=sql_query)

def set_consumer_with_error(email, error):
    conn = database()
    sql_query = 'UPDATE consumers SET error = "%s" WHERE email = "%s";' % (error, email)
    conn.query(sql=sql_query)

def set_consumer_id(email, consumer_id):
    conn = database()
    sql_query = 'UPDATE consumers SET consumer_id = "%s" WHERE email = "%s";' % (consumer_id, email)
    conn.query(sql=sql_query)

def set_consumer_with_payment_method(email):
    conn = database()
    sql_query = 'UPDATE consumers SET payment_method = 1 WHERE email = "%s";' % (email)
    conn.query(sql=sql_query)

def get_consumer_id_list():
    conn = database()
    sql_query = "SELECT consumer_id FROM consumers WHERE error IS NULL AND consumer_id IS NOT NULL ORDER BY RAND() LIMIT 1000"
    result = conn.query(sql=sql_query)

    consumer_ids = []
    for consumer_id in result:
        consumer_ids.append(consumer_id[0])

    return consumer_ids
