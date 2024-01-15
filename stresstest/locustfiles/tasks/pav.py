import json
import os
import random

from locust import HttpUser, SequentialTaskSet, events, task, between

from common.consumers import get_consumer_credit_card_id
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test
from common.testing_requests import testing_legacy_api
from common.sellers import SELLERS
from tasks.general_behaviour import GeneralTaskSet
import sys


class PavTaskSet(SequentialTaskSet):
    tasks = [GeneralTaskSet]

    @task(1)
    def pav(self):
        if 'TOKEN' not in os.environ:
            return

        self.headers = {
            'token': os.environ['TOKEN'],
            'Content-Type': 'application/json; charset=UTF-8'
        }

        credit_card_id = get_consumer_credit_card_id()

        seller_id = random.choice(SELLERS)

        seller_profile = self.get_seller_profile(seller_id)

        seller_item = self.get_item_by_store(seller_id)
        if seller_item is not None:
            seller_item_id = seller_item['data']['Item']['id']

            transaction = self.create_transaction(os.environ['PASSWORD'], seller_id, credit_card_id,
                                                  random.randint(1, 20), seller_item_id)
            if transaction is not None:
                transaction_id = transaction['data']['Transaction']['id']
                self.ack_transaction(transaction_id)

    def get_seller_profile(self, seller_id):
        payload = json.dumps({
            "profile_id": seller_id,
            "profile_type": "seller"
        })

        return testing_legacy_api(self, '/api/getProfile.json', self.headers, payload)

    def get_item_by_store(self, seller_id):
        payload = json.dumps({
            "seller_id": seller_id
        })

        return testing_legacy_api(self, '/api/itemByStoreId.json', self.headers, payload)

    def create_transaction(self, password, seller_id, credit_card_id, amount, item_id):
        payload = {
            "pin": password, "gps_acc": 4.384, "lng": -46.589675, "lat": -23.6216422, "ignore_balance": False,
            "from_explore": 0, "origin": "Profile", "biometry": False, "parcelas": "1",
            "seller_id": seller_id, "plan_type": "A", "credit_card_id": credit_card_id,
            "feed_visibility": 3,
            "itens": [{"id": item_id, "amount": "1"}], "shipping_id": "0", "shipping": "0", "address_id": "0"
        }

        pay_with_credit_card = random.randint(0, 1)

        # if pay_with_credit_card:
        #     payload["credit"] = 0
        #     payload["total"] = amount
        # else:
        #     payload["credit"] = amount
        #     payload["total"] = 0

        payload["credit"] = 0
        payload["total"] = amount

        payload = json.dumps(payload)

        return testing_legacy_api(self, '/api/createTransaction.json', self.headers, payload)

    def ack_transaction(self, transaction_id):
        payload = json.dumps({
            "transaction_id": transaction_id
        })

        return testing_legacy_api(self, '/api/ackTransaction.json', self.headers, payload)


class PavTest(HttpUser):
    tasks = [PavTaskSet]
    wait_time = between(1, 5)


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


@events.test_stop.add_listener()
def on_quitting(**kwargs):
    save_stats(scenery="pav")
    save_stats_history(scenery="pav")
    save_stats_failure(scenery="pav", errors=errors)
    notify_start_test(scenery="pav")