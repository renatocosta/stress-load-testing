import json
import os

from locust import HttpUser, SequentialTaskSet, task, between, events

from common.consumers import prepare_headers
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test
from tasks.general_behaviour import GeneralTaskSet

class CashoutBanco24HorasTaskSet(SequentialTaskSet):
    tasks = [GeneralTaskSet]
    headers = {}
    
    @task(1)
    def getInfoValues(self):
        self.headers = prepare_headers()
        self.headers['TOKEN'] = os.environ['TOKEN']
        with  self.client.get("/cashout/banco24horas/", headers=self.headers, name = "/cashout/banco24horas")  as response:
            
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
    def postAutorization(self):
        data = {
            "qr_code": "abc",
	        "withdrawal_value": 40
        }

        self.headers['password'] = "123456"

        with  self.client.post("/cashout/banco24horas/authorization/", data=json.dumps(data), headers=self.headers, name = "/cashout/banco24horas/authorization")  as response:
            
            if response.status_code == 400:
                response.failure("QR Code invalido " + str(response.status_code))
                return

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


class CashoutBanco24HorasOnLoad(HttpUser):
    tasks = [CashoutBanco24HorasTaskSet]
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
    save_stats(scenery="CashoutBanco24Horas")
    save_stats_history(scenery="CashoutBanco24Horas")
    save_stats_failure(scenery="CashoutBanco24Horas", errors=errors)
    notify_start_test(scenery="CashoutBanco24Horas")