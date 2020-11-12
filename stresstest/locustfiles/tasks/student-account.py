import json
import os

from locust import HttpUser, SequentialTaskSet, task, between, events

from common.consumers import prepare_headers
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test
from tasks.general_behaviour import GeneralTaskSet

class StudentAccountTaskSet(SequentialTaskSet):
    tasks = [GeneralTaskSet]
    headers = {}

    @task(1)
    def getStatus(self):
        self.headers = prepare_headers()
        self.headers['TOKEN'] = os.environ['TOKEN']
        with  self.client.get("/studentaccount/students/status", headers=self.headers,
                              name="/studentaccount/students/status") as response:
            print(response)
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("student-account - Error: " + str(result['Error']['description_pt']))
                return


class StudentAccountOnLoad(HttpUser):
    tasks = [StudentAccountTaskSet]
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
    save_stats(scenery="student-account")
    save_stats_history(scenery="student-account")
    save_stats_failure(scenery="student-account", errors=errors)
    notify_start_test(scenery="student-account")