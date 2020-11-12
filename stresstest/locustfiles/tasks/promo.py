from locust import HttpUser, SequentialTaskSet, events, task, between
import re, random
from locust.exception import StopUser
from faker import Faker
from common.sellers import SELLERS
import json
import os

from common.consumers import prepare_headers, set_consumer_with_error
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test
from tasks.general_behaviour import GeneralTaskSet

class PromoBehaviour(SequentialTaskSet):
    tasks = [GeneralTaskSet]

    headers = {}

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.fake = Faker('pt_BR')

    @task(1)
    def getAllConsumerData(self):
        self.headers = prepare_headers()
        self.headers['TOKEN'] = os.environ['TOKEN']

        data = {}

        with  self.client.post("/api/getAllConsumerData.json", data= json.dumps(data), headers=self.headers, name = "Get Consumer Data", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return
            result = json.loads(response.content)
            if 'data' in result and not result['data']['Consumer']['mobile_phone_verified']:
                response.failure("Consumer with empty phone")
                set_consumer_with_error(email=result['data']['Consumer']['email'], error="emptyphone")
                raise StopUser()
            else:
                response.success()
                return

    @task(1)
    def getPromotions(self):
        location = self.fake.local_latlng(country_code='BR', coords_only=True)
        url = '/promotions?latitude=%s&longitude=%s' % (location[0], location[1])
        with  self.client.get(url, headers=self.headers, name = "get promotions", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("get promotions - Error: " + str(result['Error']['description_pt']))
                return

    @task(2)
    def getPromotionsBySeller(self):
        seller_id = random.choice(SELLERS)
        with  self.client.get("/promotions/seller/" + str(seller_id), headers=self.headers, name = "get promotions by seller", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("get promotions by seller - Error: " + str(result['Error']['description_pt']))
                return


class WebsiteUser(HttpUser):
    tasks = [PromoBehaviour]
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
    save_stats(scenery="promo")
    save_stats_history(scenery="promo")
    save_stats_failure(scenery="promo", errors=errors)
    notify_start_test(scenery="promo")