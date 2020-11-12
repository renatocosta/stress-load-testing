from locust import HttpUser, SequentialTaskSet, task, events

from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class UserBehavior(SequentialTaskSet):

    @task(1)
    def homePage(self):
        with self.client.get("/site", name = "Home Page", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(5, 9)



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
    save_stats(scenery="site")
    save_stats_history(scenery="site")
    save_stats_failure(scenery="site", errors=errors)
    notify_start_test(scenery="site")