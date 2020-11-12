import os
from locust import HttpUser, SequentialTaskSet, events, task, between
from faker import Faker

from common.consumers import prepare_headers
from tasks.general_behaviour import GeneralTaskSet
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class SearchTaskSet(SequentialTaskSet):
    tasks = [GeneralTaskSet]

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.fake = Faker('pt_BR')

    @task(1)
    def getFeed(self):
        self.headers = prepare_headers()
        self.headers['TOKEN'] = os.environ['TOKEN']

        self.client.post("/api/getFeed.json", "", headers=self.headers, name = "Get feed")

    @task(1)
    def searchStore(self):
        with self.client.get("/search?group=STORE&latitude=-20.31909910100617&longitude=-40.33056855472962&page=0", headers=self.headers, name = "Search Store", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return

    @task(1)
    def searchMain(self):
        with self.client.get("/search?group=MAIN&latitude=-20.31909910100617&longitude=-40.33056855472962&page=0", headers=self.headers, name = "Search Main", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return

    @task(1)
    def searchName(self):
        with self.client.get("/search?group=MAIN&latitude=-20.31905414630407&longitude=-40.33056382796243&page=0&term=" + self.fake.name(), headers=self.headers, name = "Search Name on Main", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return

    @task(1)
    def searchName(self):
        with self.client.get("/search?group=CONSUMERS&term=" + self.fake.name(), headers=self.headers, name = "Search Name on Consumers", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return


class SearchTest(HttpUser):
    tasks = [SearchTaskSet]
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
    save_stats(scenery="search")
    save_stats_history(scenery="search")
    save_stats_failure(scenery="search", errors=errors)
    notify_start_test(scenery="search")
