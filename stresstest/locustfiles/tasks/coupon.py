from locust import HttpUser, SequentialTaskSet, task, between, events
from locust.exception import StopUser
import json
import os

from common.consumers import prepare_headers, set_consumer_with_error
from tasks.general_behaviour import GeneralTaskSet
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class CouponBehaviour(SequentialTaskSet):
    tasks = [GeneralTaskSet]

    headers = {}

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
    def addPromoCoupon(self):

        data = {
            "referral_code": os.environ["testing_PROMO_COUPON"]
        }

        with  self.client.post("/api/validateReferralCode.json", data=json.dumps(data), headers=self.headers, name = "add Promo Coupon", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("add Promo Coupon - Error: " + str(result['Error']['description_pt']))
                return

#todo
    # @task(1)
    # def addMGMCoupon(self):

    #     data = {
    #         "referral_code": "GC3SNA"
    #     }

    #     with  self.client.post("/api/validateReferralCode.json", data=json.dumps(data), headers=self.headers, name = "add MGM Coupon", catch_response=True)  as response:
    #         if response.status_code != 200:
    #             response.failure("Got wrong response code " + str(response.status_code))
    #             raise StopLocust()
    #         if response.content is None:
    #             response.failure("Response is empty")
    #             raise StopLocust()
    #         result = json.loads(response.content)
    #         if 'Error' in result:
    #             response.failure("add MGM Coupon - Error: " + str(result['Error']['description_pt']))
    #             return


class CouponUser(HttpUser):
    tasks = [CouponBehaviour]
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
    save_stats(scenery="coupon")
    save_stats_history(scenery="coupon")
    save_stats_failure(scenery="coupon", errors=errors)
    notify_start_test(scenery="coupon")
