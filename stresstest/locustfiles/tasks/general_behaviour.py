import json
import os
from locust import SequentialTaskSet, task, HttpUser, between

from common.testing_requests import get_headers, testing_legacy_api
from common.auth import set_consumer_credentials


class GeneralTaskSet(SequentialTaskSet):

    def on_start(self):
        set_consumer_credentials(self)

    @task(1)
    def get_all_consumer_data(self):

        if 'TOKEN' not in os.environ:
            return

        headers = {'token': os.environ['TOKEN']}
        data = json.dumps({})
        consumer_data = testing_legacy_api(self, '/api/getAllConsumerData.json', headers, data)
        os.environ['CONSUMER_DATA'] = json.dumps(consumer_data)

    @task(2)
    def search_requests(self):

        if 'TOKEN' not in os.environ:
            return

        headers = get_headers()
        headers['token'] = os.environ['TOKEN']
        with self.client.get('/search',
                             params={
                                 'group': 'SUGGESTIONS'
                             },
                             headers=headers,
                             timeout=30,
                             name='/search',
                             catch_response=True
                             ) as response:

            if response.status_code != 200:
                return response.failure("Status code other than 200")

            result = json.loads(response.content)

            if 'Error' in result:
                return response.failure("Got wrong response: " + result['Error']['description_pt'])

            return result

    @task(1)
    def get_global_credit(self):

        if 'TOKEN' not in os.environ:
            return

        headers = {'token': os.environ['TOKEN']}
        data = json.dumps({})
        testing_legacy_api(self, '/api/getGlobalCredit.json', headers, data)

    @task(2)
    def get_feed(self):

        if 'TOKEN' not in os.environ:
            return

        headers = {'token': os.environ['TOKEN']}
        data = json.dumps({'visibility': '3'})

        #all feeds
        response = testing_legacy_api(self, '/api/getFeed.json', headers, data)
        feed_list = False
        if response is not None:
            feed_list = response['data']['feed']

        if feed_list:
            last_id = feed_list[-1]['Data']
            data = json.dumps({'visibility': '3', 'start_id': last_id})
            testing_legacy_api(self, '/api/getFeed.json', headers, data, name='roll feed')

            # # get comment
            # data = json.dumps({'feed_common_data_id': last_id})
            # testing_legacy_api(self, 'api/getFeedComments.json', headers, data, name='get feed comments')

        #only me feeds
        data = json.dumps({'visibility': '1'})
        testing_legacy_api(self, '/api/getFeed.json', headers, data, name='feed only me')

    @task(1)
    def get_payment_methods(self):

        if 'TOKEN' not in os.environ:
            return

        headers = {'token': os.environ['TOKEN']}
        data = json.dumps({})
        payment_methods = testing_legacy_api(self, '/api/getPaymentMethods.json', headers, data)
        os.environ['PAYMENT_METHODS'] = json.dumps(payment_methods)

    @task(1)
    def stop(self):
        self.interrupt()


class GeneralBehaviour(HttpUser):
    tasks = [GeneralTaskSet]
    wait_time = between(1, 2)


