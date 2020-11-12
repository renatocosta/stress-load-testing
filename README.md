# Faustão Stresstesting Framework

## IMPORTANT
This tool is designed to run in PRODUCTION environment.

## Description
Faustão is a distributed load testing framework, created to take advantage of [Kubernetes](https://github.com/kubernetes/kubernetes) as a platform for auto-scaling the load generators and [Airflow](https://github.com/apache/airflow) as an orchestrating tool. The tests are written in Python, using [Locust](https://github.com/locustio/locust) as it's main tool


## Organization
Test cases are placed in `stresstest/locustfiles/tasks`, to activate a test case you need to create it's helm subchart in [faustao framework](https://github.com/PicPay/faustao-framework) and [schedule it](loadtest-schedule.yaml).
Faustão will run in a kubernetes cluster according to schedule and (soon) then output the result in slack/a functional dashboard (tbd).


## Basic Usage
Once your test is scheduled, take note of when it will run and collect APM metrics, machines consumption dashboards and every other piece of technology your test will touch, this can generate severe improvement backlog.


## Working Scenarios
- Add Consumer
- Feed
- Search
- Promo
- Site