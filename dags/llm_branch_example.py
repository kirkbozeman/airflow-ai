"""Example of @task.llm_branch: the LLM routes to one of several downstream tasks.

Downstream task IDs are discovered automatically from the DAG topology and presented to the LLM as
the set of valid choices.
"""

import logging
import random
from datetime import datetime

from airflow.decorators import dag, task

log = logging.getLogger(__name__)


@dag(
    dag_id="llm_branch_example",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["claude"],
)
def llm_branch_example():

    @task
    def generate_random_letter() -> str:
        return random.choice(["A", "B", "C"])

    @task.llm_branch(
        llm_conn_id="anthropic_default",
        system_prompt="Route to the task matching the given letter.",
    )
    def pick_branch(letter: str):
        """Note that the tasks are actually named task_<a|b|c>, so the LLM has to infer the correct
        task from A, B, and C.

        This fuzziness is fine here but would be a bit iffy in a prod env.
        """
        return f"Route to {letter.lower()}."

    @task
    def task_a():
        log.info("Ran A")

    @task
    def task_b():
        log.info("Ran B")

    @task
    def task_c():
        log.info("Ran C")

    pick_branch(generate_random_letter()) >> [task_a(), task_b(), task_c()]


llm_branch_example()
