import json
import os
import csv
from common.database import database
from locust import runners
import slack
import sys

def notify_start_test(scenery="add-consumer"):
    # Só envia mensagem e reports em prod
    # if "appgw.picpay.com" not in os.environ["TARGET_HOST"]:
    #     return False
    if not isinstance(runners.Runner, runners.MasterRunner):
        return False

    slack_token = os.environ["SLACK_API_TOKEN"]
    channel = os.environ["SLACK_CHANNEL"]
    client = slack.WebClient(token=slack_token)

    response = client.chat_postMessage(
      channel=channel,
      text="Hello! O cenario de teste: "+scenery+" terminou :tada::beers:",
      as_user=True
    )

    send_file(file_path="/tmp/lt_stats.csv", title="Stats - " + scenery)
    send_file(file_path="/tmp/lt_stats_history.csv", title="Stats History- " + scenery)
    send_file(file_path="/tmp/lt_failures.csv", title="Failures - " + scenery)


def send_file(file_path, title, retry=0):
    slack_token = os.environ["SLACK_API_TOKEN"]
    channel = os.environ["SLACK_CHANNEL"]
    client = slack.WebClient(token=slack_token)

    if os.path.exists(file_path):
        response = client.files_upload(
          channels=channel,
          file=open(file_path, 'rb'),
          filename=os.path.basename(file_path),
          title=title
        )

        if response['ok'] == False and retry <= 3:
            print("tentando enviar o arquivo " + file_path + " pela " + str(retry) + "vez")
            retry = retry + 1
            send_file(file_path=file_path, title=title, retry=retry)


def save_stats(scenery):
    csv_data = csv.reader(open('/tmp/lt_stats.csv'))
    conn = database()
    i = 0
    for row in csv_data:
        if i == 0:
            i = 1
            continue

        sql_query = 'INSERT INTO stats (scenery, type, name, requests, failures, median_response_time, average_response_time, min_response_time, max_response_time, average_content_size, requests_per_second, requests_failed_per_second, 50_percent, 66_percent, 75_percent, 80_percent, 90_percent, 95_percent, 98_percent, 99_percent, 999_percent, 9999_percent, 100_percent) VALUES ("' + scenery +'","'+ '","'.join(row) +'")'
        conn.query(sql=sql_query)


def save_stats_history(scenery):
    csv_data = csv.reader(open('/tmp/lt_stats_history.csv'))
    conn = database()
    i = 0
    for row in csv_data:
        if i == 0:
            i = 1
            continue

        sql_query = 'INSERT INTO stats_history VALUES(NULL, "'+scenery+'", NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        conn.query(sql=sql_query, params=row)


def save_stats_failure(scenery, errors):
    conn = database()
    for key in errors:
        row = errors[key]
        query = 'INSERT INTO stats_failure VALUES(NULL, "%s", NULL, "%s", "%s", "%s")' % (scenery, row["type"], row["exception"], row["count"])
        conn.query(sql=query)