import json
import os

from locust import HttpUser, SequentialTaskSet, task, between, events
from faker import Faker

from common.consumers import prepare_headers
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test
from tasks.general_behaviour import GeneralTaskSet

class CardRegistrationTaskSet(SequentialTaskSet):
    tasks = [GeneralTaskSet]
    headers = {}

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.fake = Faker('pt_BR')

    @task(1)
    def getAccount(self):
        self.headers = prepare_headers()
        self.headers['TOKEN'] = os.environ['TOKEN']

        with  self.client.get("/credit/account?complete=0", headers=self.headers, name = "Get Account Card Registration")  as response:
            
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("GetAccountCardRegistration - Error: " + str(result['Error']['description_pt']))
                return

    @task(1)
    def getCreditRegistration(self):
        with self.client.get("/credit/registration", headers=self.headers, name = "Get Credit Registration")  as response:
        
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("GetCardRegistration - Error: " + str(result['Error']['description_pt']))
                return


class CardRegistrationTest(HttpUser):
    tasks = [CardRegistrationTaskSet]
    wait_time = between(1, 1)


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
    save_stats(scenery="card-registration")
    save_stats_history(scenery="card-registration")
    save_stats_failure(scenery="card-registration", errors=errors)
    notify_start_test(scenery="card-registration")