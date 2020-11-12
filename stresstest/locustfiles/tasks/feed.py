import os
from locust import HttpUser, SequentialTaskSet, task, between, events

from common.consumers import prepare_headers
from tasks.general_behaviour import GeneralTaskSet
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class FeedTaskSet(SequentialTaskSet):
    tasks = [GeneralTaskSet]
    @task(1)
    def get_feed(self):
        self.headers = prepare_headers()
        self.headers['TOKEN'] = os.environ['TOKEN']

        self.client.post("/api/getFeed.json", "", headers=self.headers, name="Get feed")


class FeedTest(HttpUser):
    tasks = [FeedTaskSet]
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
    save_stats(scenery="feed")
    save_stats_history(scenery="feed")
    save_stats_failure(scenery="feed", errors=errors)
    notify_start_test(scenery="feed")