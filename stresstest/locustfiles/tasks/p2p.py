from locust import HttpUser, SequentialTaskSet, events, task, between
import random
from locust.exception import StopUser
import json
import os

from common.consumers import prepare_headers, get_consumer_id_list
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test
from tasks.general_behaviour import GeneralTaskSet


class P2PBehaviour(SequentialTaskSet):
    tasks = [GeneralTaskSet]

    headers = {}
    profileId = 0
    creditCardId = 0

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.payee_id = get_consumer_id_list()

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
            if 'data' in result:
                response.success()
                return

    @task(1)
    def getPaymentMethods(self):
        data = {}

        with  self.client.post("/api/getPaymentMethods.json", data= json.dumps(data), headers=self.headers, name = "Get Payment Methods", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return
            result = json.loads(response.content)
            if 'data' in result:
                if len(result['data']['PaymentMethods']) > 0:
                    # Pega o primeiro cartao de credito cadastrado
                    self.creditCardId = result['data']['PaymentMethods'][0]['id']
                    response.success()
                    return
                else:
                    response.failure("Got wrong response: User whitout credit card")
                    raise StopUser()

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
    def searchStore(self):
        with self.client.get("/search?group=SUGGESTIONS", headers=self.headers, name = "Search Store", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return

    @task(1)
    def getGlobalCredit(self):
        with  self.client.post("/api/getGlobalCredit.json", "", headers=self.headers, name = "Get global credit", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()

    @task(1)
    def getFeed(self):
        data = {"visibility":"3"}
        self.client.post("/api/getFeed.json", data=json.dumps(data), headers=self.headers, name = "Get feed")

    @task(1)
    def notificationsToken(self):
        data = {"token": "xpto"}
        self.client.put("/notifications/token", data=json.dumps(data), headers=self.headers, name = "Notifications token")

    @task(1)
    def getGlobalCreditAfterNotificationToken(self):
        with  self.client.post("/api/getGlobalCredit.json", "", headers=self.headers, name = "Get global credit after notifications Token", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()

    @task(1)
    def createP2PTransaction(self):
        payee_id = self.payee_id[random.randint(0, len(self.payee_id))]

        data = {
            "consumer_value":"1.0",
            "credit":"0",
            "consumer_credit_card_id": self.creditCardId,
            "feed_visibility":3,
            "ignore_balance":"true",
            "message":"",
            "origin":"Lista",
            "payee_id": payee_id,
            "pin":"1234",
            "parcelas":"1",
            "surcharge":0.0,
            "biometry":"false"
        }

        self.headers['force_response'] = 'ok'
        with  self.client.post("/api/createP2PTransaction.json", data=json.dumps(data), headers=self.headers, name = "Create P2P Transaction", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("Create P2P Transaction - Error: " + str(result['Error']['description_pt']))
                return

    @task(1)
    def getGlobalCreditAfterP2PTransaction(self):
        with  self.client.post("/api/getGlobalCredit.json", "", headers=self.headers, name = "Get global credit after P2P transaction", catch_response=True)  as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()

    @task(1)
    def getFeedAfterP2PTransaction(self):
        data = {"visibility": "2"}
        self.client.post("/api/getFeed.json", data=json.dumps(data), headers=self.headers, name = "Get feed after P2P transaction")

    @task(1)
    def getFeedAfterP2PTransactionWithVisibility3(self):
        data = {"visibility": "3"}
        self.client.post("/api/getFeed.json", data=json.dumps(data), headers=self.headers, name = "Get feed after P2P transaction with visibility 3")


class P2PUser(HttpUser):
    tasks = [P2PBehaviour]
    wait_time = between(1, 5)


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
    save_stats(scenery="p2p")
    save_stats_history(scenery="p2p")
    save_stats_failure(scenery="p2p", errors=errors)
    notify_start_test(scenery="p2p")