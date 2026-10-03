"""This is an example of utilizing task.llm_sql with Anthropic API to generate SQL from a question.

The generated SQL is logged; it is not executed.
"""

import logging
from datetime import datetime

from airflow.decorators import dag, task

log = logging.getLogger(__name__)


@dag(
    dag_id="llm_sql_example",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["claude"],
)
def llm_sql_example():
    @task.llm_sql(
        llm_conn_id="anthropic_default",
        db_conn_id="dwh_default",
        dialect="postgres",
    )
    def question_to_sql(question: str):
        return question

    @task
    def log_sql(sql: str):
        log.info("Generated SQL:\n%s", sql)

    sql = question_to_sql("How many solos are in the database for each style?")
    log_sql(sql)


llm_sql_example()
