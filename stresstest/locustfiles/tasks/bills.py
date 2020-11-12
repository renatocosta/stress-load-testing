import json
import os

from locust import HttpUser, SequentialTaskSet, task, between
from locust.exception import StopUser

from tasks.general_behaviour import GeneralTaskSet
from common.consumers import prepare_headers


class BillsTaskSet(SequentialTaskSet):
    tasks = [GeneralTaskSet]

    @task(1)
    def bills(self):

        if 'TOKEN' not in os.environ:
            return

        code = '10499712012251770123545678901518499370000000001'
        result = self.read_bar_code(code)

        bill_amount = result['amount']
        self.pay_bill(code, bill_amount)

    def pay_bill(self, code, bill_amount):
        consumer_data = json.loads(os.environ['CONSUMER_DATA'])
        consumer_credit_card = 0
        if len(consumer_data['data']['ConsumerCreditCard']) > 0:
            # Pega o primeiro cartao de credito cadastrado
            consumer_credit_card = consumer_data['data']['ConsumerCreditCard'][0]['id']

        headers = {
            'token': os.environ['TOKEN'],
            'password': os.environ['PASSWORD'],
            'Content-Type': 'application/json; charset=UTF-8'
        }

        payload = {
            "biometry": False,
            "code": code,
            "credit_card_id": consumer_credit_card,
            "credit": bill_amount,
            "description": "boleto teste ",
            "duplicated": "0",
            "feed_visibility": "3",
            "parcelas": 1,
            "origin": "Feed",
            "total": "0.00"
        }

        with self.client.post('/bills/v2/payment',
                              data=json.dumps(payload),
                              headers=headers,
                              timeout=30,
                              name='/bills', catch_response=True) as response:

            result = json.loads(response.content)

            if consumer_credit_card == 0:
                response.failure("Got wrong response: User whitout credit card")
                raise StopUser()

            if 'Error' in result:
                return response.failure("Got wrong response: " + result['Error']['description_pt'])

            return result

    def read_bar_code(self, code):
        headers = {
            'token': os.environ['TOKEN']
        }

        with self.client.get('/bills/barcode?code=' + code,
                             headers=headers,
                             timeout=30,
                             name='/bills', catch_response=True) as response:

            if response.status_code != 200:
                return response.failure("Status code other than 200")

            result = json.loads(response.content)

            if 'Error' in result:
                return response.failure("Got wrong response: " + result['Error']['description_pt'])

            return result


class BillsTest(HttpUser):
    tasks = [BillsTaskSet]
    wait_time = between(1, 3)
