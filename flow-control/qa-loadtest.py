from airflow import DAG
import dagfactory

dag_factory = dagfactory.DagFactory("/opt/airflow/dags/qa-loadtest-schedule.yaml")

dag_factory.clean_dags(globals())
dag_factory.generate_dags(globals())