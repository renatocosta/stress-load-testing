import json
import random
from common.consumers import prepare_headers


def testing_legacy_api(task_set, endpoint, headers, payload, name=None):

    if name is None:
        name = endpoint

    with task_set.client.post(
            endpoint,
            data=payload,
            headers=headers,
            name=name,
            catch_response=True
    ) as response:
        if response.status_code != 200:
            return response.failure("Status code other than 200")

        result = json.loads(response.content)

        if 'Error' in result:
            return response.failure("Got wrong response: " + result['Error']['description_pt'])

        if result is None:
            return response.failure("Got None response")

        return result


def get_headers():
    return prepare_headers()
