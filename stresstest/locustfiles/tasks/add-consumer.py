from locust import HttpUser, SequentialTaskSet, events, task, between
import random
from locust.exception import StopUser
from faker import Faker
import json
import datetime
import os
import logging

from common.consumers import prepare_headers, MAX_USERS, save_consumer_load_test_credentials, set_consumer_with_error, set_consumer_id
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class UserBehavior(SequentialTaskSet):
    token = ""
    headers = {}
    smsCodeVerification = ""
    contacts = {
        "contacts": []
    }

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.fake = Faker('pt_BR')
        self.headers = prepare_headers()

    @task(1)
    def validate_name(self):
        headers = self.headers.copy()
        headers['content-type'] = "application/x-www-form-urlencoded"

        data = {
            "name": "Load Test " + self.fake.name()
        }

        with self.client.post("/api/isValidName.json", data=data, headers=headers, name="Validate Name", catch_response=True) as response:
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
    def send_sms_verification(self):

        phone_number = "99" + str(random.randint(1000000, 9000000))
        data = {
            "ddd": str("29"),
            "number": phone_number,
            "ccr": self.fake.uuid4(),
            "rpspd": "false"
        }

        with self.client.post("/api/sendSmsVerification.json", data=json.dumps(data), headers=self.headers, name="Send Sms Verification", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()
            result = json.loads(response.content)
            if 'data' in result:
                response.success()
                return
            if 'Error' in result and result['Error']['id'] == "2001":
                if len(self.contacts['contacts']) <= 1000:
                    contact = [
                        self.fake.name(),
                        [phone_number],
                        []
                    ]
                    self.contacts['contacts'].append(contact)

                self.smsCodeVerification = result['Error']['description_pt'].replace("Code ", "")
                response.success()
                return
            if 'Error' in result:
                response.failure("verifyPhoneNumber - Error: " + str(result['Error']['description_pt']))
                raise StopUser()

    @task(1)
    def verify_phone_number(self):
        data = {
            "verification_code": self.smsCodeVerification,
            "auto_validate":0
        }

        with self.client.post("/api/verifyPhoneNumber.json", data=json.dumps(data), headers=self.headers, name="Verify Phone Number", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()
            result = json.loads(response.content)
            if 'data' in result:
                response.success()
            if 'Error' in result:
                response.failure("verifyPhoneNumber - Error: " + str(result['Error']['description_pt']))
                raise StopUser()

    @task(1)
    def validate_email(self):
        data = {
            "email": 'customer_load_test_' + str(random.randint(1, 10000)) + '@testing.test'
        }

        with self.client.post("/api/isValidEmail.json", data=json.dumps(data), headers=self.headers, name="Validate email", catch_response=True) as response:
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
    def validate_pass(self):
        data = {
            "pass": self.fake.password(length=random.randint(4, 10), special_chars=True, digits=True, upper_case=True, lower_case=True)
        }

        with self.client.post("/api/isValidPass.json", data= json.dumps(data), headers=self.headers, name="Validate Password", catch_response=True) as response:
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
    def add_consumer(self):
        data = {
            "name": "Load Test " + self.fake.name(),
            "email": 'customer_load_test_' + str(random.randint(1, MAX_USERS)) + '@testing.test',
            "pass": "1234",
            "cpf": "99988877766",
            "birth_date": self.fake.date("%d/%m/%Y", datetime.date(2000, 12, 31)),
            "referrer": "",
            "distinct_id": self.fake.uuid4(),
            "notification_token": ""
        }

        #logging.info(data)
        with self.client.post("/api/addConsumer.json", data= json.dumps(data), headers=self.headers, name="Add Consumer", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()
            result = json.loads(response.content)
            if 'data' in result:
                self.token = result['data']['token']
                save_consumer_load_test_credentials(email=data['email'], name=data['name'], password=data['pass'])

                response.success()
                return
            if 'Error' in result and result['Error']['id'] == "5018":
                response.success()
                return
            if 'Error' in result:
                response.failure("addConsumer - Error: " + str(result['Error']['description_pt']))
                raise StopUser()

    @task(1)
    def get_all_consumer_data(self):
        self.headers['token'] = self.token
        data = {}

        with self.client.post("/api/getAllConsumerData.json", data=json.dumps(data), headers=self.headers, name="Get Consumer Data", catch_response=True) as response:
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
                set_consumer_id(email=result['data']['Consumer']['email'], consumer_id=result['data']['Consumer']['id'])
                return

    @task(1)
    def identify_contacts(self):
        # logging.info(self.contacts)
        with self.client.post("/api/identifyContacts.json", data=json.dumps(self.contacts), headers=self.headers, name="Identify Contacts", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
                raise StopUser()
            if response.content is None:
                response.failure("Response is empty")
                raise StopUser()

    @task(1)
    def add_promo_coupon(self):
        data = {
            "referral_code": os.environ["testing_PROMO_COUPON"]
        }

        with self.client.post("/api/validateReferralCode.json", data=json.dumps(data), headers=self.headers, name="Add Promo Coupon", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Got wrong response code " + str(response.status_code))
            if response.content is None:
                response.failure("Response is empty")
            result = json.loads(response.content)
            if 'Error' in result:
                response.failure("add Promo Coupon - Error: " + str(result['Error']['description_pt']))
                return


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(4, 10)


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
def quitting(**kwargs):
    save_stats(scenery="add-consumer")
    save_stats_history(scenery="add-consumer")
    save_stats_failure(scenery="add-consumer", errors=errors)
    notify_start_test(scenery="add-consumer")