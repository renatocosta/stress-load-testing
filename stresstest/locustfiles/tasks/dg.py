import json
import os
from random import randint, choice

from locust import HttpUser, SequentialTaskSet, task, events, between

from common.consumers import get_consumer_credit_card_id
from common.testing_requests import testing_legacy_api
from tasks.general_behaviour import GeneralTaskSet
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class DGTaskSet(SequentialTaskSet):
    tasks = [GeneralTaskSet]

    @task(2)
    def dg(self):
        if 'TOKEN' not in os.environ:
            return

        self.headers = {
            'token': os.environ['TOKEN'],
            'Content-Type': 'application/json; charset=UTF-8',
            'device_os':  choice(['android', 'ios']),
            'app_version': choice(['10.7.0', '10.16.0'])
        }

        self.services = {
            'sky_tv': {
                'id': '5ab28951bae100048b7dfee3',
                'products': [
                    {
                        'type': 'tvrecharges',
                        'product_id': '5c6abfd384b99800330cfd32',
                        'subscriber_code': '1111111111111',
                        'amount': '18.9'
                    }
                ]
            },
            'steam': {
                'id': '5a27161ece45a600350a76e2',
                'products': [
                    {
                        'type': 'digitalcodes',
                        'product_id': '5a27161ece45a600350a76e6',
                        'amount': '10.0'
                    }
                ]
            }
        }

        self.open_store()
        transaction = self.create_transaction(os.environ['PASSWORD'], get_consumer_credit_card_id())

        if transaction is not None:
            transaction_id = transaction['data']['Transaction']['id']
            self.ack_transaction(transaction_id)

    def open_store(self):
        with self.client.get('/search',
                             params={
                                 'group': 'STORE',
                                 'page': randint(0, 1)
                             },
                             headers=self.headers,
                             timeout=30,
                             name='/search_store',
                             catch_response=True
                             ) as response:

            if response.status_code != 200:
                return response.failure('Status code other than 200')

            result = json.loads(response.content)

            if 'Error' in result:
                return response.failure('Got wrong response: ' + result['Error']['description_pt'])

            return result

    def open_products(self):
        print(self.headers)
        with self.client.get('/digitalgoods/digitalcodes/products',
                             params={
                                 'service_id': choice(self.services_id),
                                 'page': randint(0, 1)
                             },
                             headers=self.headers,
                             timeout=30,
                             name='/search_store',
                             catch_response=True
                             ) as response:

            if response.status_code != 200:
                return response.failure('Status code other than 200')

            result = json.loads(response.content)

            if 'Error' in result:
                return response.failure('Got wrong response: ' + result['Error']['description_pt'])

            return result

    def create_transaction(self, password, credit_card_id):
        digital_good = choice(list(self.services.keys()))
        digital_good_info = self.services[digital_good]
        digital_goods_service_id = digital_good_info['id']
        digital_good_product = choice(digital_good_info['products'])
        amount = digital_good_product['amount']

        payload = {'pin': password, 'gps_acc': 0, 'lng': 0, 'lat': 0, 'ignore_balance': False, 'from_explore': 0,
                   'origin': 'DigitalGoods', 'biometry': False, 'parcelas': '1', 'seller_id': '14370',
                   'plan_type': 'A', 'credit_card_id': credit_card_id, 'feed_visibility': 3,
                   'id_digitalgoods': digital_goods_service_id,
                   'digitalgoods': digital_good_product, 'shipping_id': '0', 'shipping': '0', 'address_id': '0'}

        pay_with_credit_card = randint(0, 1)

        if pay_with_credit_card:
            payload['credit'] = 0
            payload['total'] = amount
        else:
            payload['credit'] = amount
            payload['total'] = 0

        payload = json.dumps(payload)

        return testing_legacy_api(self, '/api/createTransaction.json', self.headers, payload, name='buying ' + digital_good)

    def ack_transaction(self, transaction_id):
        payload = json.dumps({
            'transaction_id': transaction_id
        })

        return testing_legacy_api(self, '/api/ackTransaction.json', self.headers, payload)


class DGTest(HttpUser):
    tasks = [DGTaskSet]
    wait_time = between(1, 3)


errors = {}


@events.request_failure.add_listener
def request_failure_handler(request_type, name, response_time, exception, **kwargs):
    key_name = name.strip().lower().replace(" ", "_")

    if key_name not in errors:
        errors[key_name] = {}
        errors[key_name]["count"] = 0
        errors[key_name]["type"] = request_type
        errors[key_name]["exception"] = exception

    errors[key_name]["count"] += 1


@events.test_stop.add_listener
def on_quitting(**kwargs):
    save_stats(scenery="dg")
    save_stats_history(scenery="dg")
    save_stats_failure(scenery="dg", errors=errors)
    notify_start_test(scenery="dg")