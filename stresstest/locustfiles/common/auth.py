import json
import os
from locust.exception import StopUser
from common.picpay_requests import picpay_legacy_api, get_headers
from common.database import database
from common.consumers import set_consumer_with_error
import sys


def set_consumer_credentials(task_set):
    email = get_consumer_load_test_credentials()
    password = "1234"
    user = {"email": email, "password": password}

    result = picpay_legacy_api(task_set, '/api/userLogin.json', get_headers(), json.dumps(user))

    if result is None:
        raise StopUser()

    if 'Error' in result:
        raise StopUser()
    if 'data' not in result:
        raise StopUser()

    os.environ['TOKEN'] = result['data']
    os.environ['EMAIL'] = email
    os.environ['PASSWORD'] = password


def get_consumer_load_test_credentials():
    conn = database()

    sql = "SELECT email FROM consumers WHERE error IS NULL ORDER BY RAND() LIMIT 1"
    if os.environ['NEED_PAYMENT_METHOD'] == "true":
        sql = 'SELECT email FROM consumers WHERE error IS NULL AND payment_method = 1 ORDER BY RAND() LIMIT 1'

    email = conn.fetchone(sql)

    if email is None:
        print("No users found")
        raise StopUser()

    return email[0]
