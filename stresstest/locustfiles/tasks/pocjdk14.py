from locust import HttpUser, SequentialTaskSet, events, between, task
import random
from faker import Faker
import json
from random import randint, choice
from common.consumers import prepare_headers, MAX_USERS, save_consumer_load_test_credentials, set_consumer_with_error
from common.reports import save_stats, save_stats_history, save_stats_failure, notify_start_test


class CustomerTaskSet(SequentialTaskSet):
    headers = {
        'Content-Type': 'application/json',
        'Accept-Encoding':'gzip'
    }

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.fake = Faker('pt_BR')
        self.name = self.fake.name()

    def generate_cpf(self):
        cpf = [random.randint(0, 9) for x in range(9)]

        for _ in range(2):
            val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11

            cpf.append(11 - val if val > 1 else 0)

        return '%s%s%s.%s%s%s.%s%s%s-%s%s' % tuple(cpf)

    @task(1)
    def create_constumer(self):
        data = {
            "email": "load.test" + self.fake.email(),
            "name": "Load Test " + self.fake.name(),
            "password": "1234",
            "cpf": str(self.generate_cpf())
        }
    
        with  self.client.post("/customers", data=json.dumps(data), headers= self.headers,  name = "Create Customer", catch_response=True)  as response:
            if response.status_code != 201:
                response.failure("Got wrong response code " + str(response.status_code))
                return
            if response.content is None:
                response.failure("Response is empty")
                return
            
            if response.status_code == 201:
                save_consumer_load_test_credentials(email=data['email'], name=data['name'], password=data['password'])
                response.success()
                return
    
    @task(1)
    def find_paginate_customer(self):
        limit = choice([55,100,120,240,250,300,450,500])
        name = choice(["Dr","Jo","Lu", "Ma", "R", "A", "Tes","B", "C", "D"])
        page = choice([0,1])
        sorter = str(choice(["MOST_RECENT", "LEAST_RECENT"]))
    
        url = "/customers/paginate?limit={}&name={}&page={}&sorter={}".format(limit,name,page,sorter)
        with  self.client.get(str(url), headers= self.headers, name = "Find Paginate Customer", catch_response=True)  as response:
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
    def update_customer(self):
        customerId = randint(1,37000)
        url = "/customers/{}".format(customerId)
        
        data = {
            "email": "update" + self.fake.email(),
            "name": "UPDATE  " + self.fake.name(),
            "password": "4321"
            # "cpf": str(self.generate_cpf())
        }
        
        with self.client.put(str(url), data=json.dumps(data), headers= self.headers, name = "Update Customer", catch_response=True)  as response:
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
               

class WebsiteUser(HttpUser):
    tasks = [CustomerTaskSet]
    wait_time = between(1, 2)


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
def on_quitting():
    save_stats(scenery="pocjdk14")
    save_stats_history(scenery="pocjdk14")
    save_stats_failure(scenery="pocjdk14", errors=errors)
    notify_start_test(scenery="pocjdk14")