from locust import HttpUser, SequentialTaskSet, task, events,between

from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class UserBehavior(SequentialTaskSet):

    @task(1)
    def homePage(self):
        with self.client.get("/loadtest", name = "Load Test Gateway", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
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
    save_stats(scenery="gateway")
    save_stats_history(scenery="gateway")
    save_stats_failure(scenery="gateway", errors=errors)
    notify_start_test(scenery="gateway")