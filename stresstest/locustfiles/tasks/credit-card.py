from locust import HttpUser, SequentialTaskSet, task, between, events
import random
from locust.exception import StopUser
from faker import Faker
import json
import os

from common.consumers import prepare_headers, set_consumer_with_payment_method
from tasks.general_behaviour import GeneralTaskSet
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class CardBehaviour(SequentialTaskSet):
    tasks = [GeneralTaskSet]

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
            print(result)
            if 'data' in result:
                self.email = result['data']['Consumer']['email']

                response.success()
                return

    @task(1)
    def updateDeviceDetails(self):

        data = {
            "permission_contacts": "false",
            "permission_camera": "false",
            "permission_sms": "false",
            "permission_storage": "false",
            "permission_location": "false"
        }

        with  self.client.post("/api/updateDeviceDetails.json", data=json.dumps(data), headers=self.headers, name = "Update device details", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()


    @task(1)
    def insertCreditCard(self):
        card_types = ["mastercard", "visa16"]
        card = card_types[random.randint(0, 1)]
        phone_number = "99" + str(random.randint(1000000, 9000000))

        data = {
            "card_holder": self.fake.name(),
            "card_number": self.fake.credit_card_number(card_type=card),
            "cvv": self.fake.credit_card_security_code(card_type=card),
            "expiry_date": self.fake.credit_card_expire(start="now", end="+20y", date_format="%m/%y"),
            "holder_cpf": self.fake.cpf(),
            "holder_phone": "29" + phone_number,
            "scanned": "false",
            "alias": card + " load teste",
            "number": random.randint(10, 2000),
            "street": self.fake.street_name(),
            "zip_code": self.fake.postcode(),
            "complement": "",
            "cidade": self.fake.city(),
            "uf": self.fake.estado_sigla()
        }

        self.headers['force_response'] = 'ok'
        with  self.client.post("/api/insertCreditCard.json", data=json.dumps(data), headers=self.headers, name = "Insert credit card", catch_response=True)  as response:
            print(response.status_code)
            print(response.content)
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("insertCreditCard - Error: " + str(result['Error']['description_pt']))
                return

            set_consumer_with_payment_method(self.email)


class CardUser(HttpUser):
    tasks = [CardBehaviour]
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
    save_stats(scenery="addcard")
    save_stats_history(scenery="addcard")
    save_stats_failure(scenery="addcard", errors=errors)
    notify_start_test(scenery="addcard")