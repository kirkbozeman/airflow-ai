"""This is an example of utilizing task.agent with Anthropic API, specifically the SQLToolset."""

import logging
from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.common.ai.toolsets.sql import SQLToolset
from pydantic_ai.usage import UsageLimits

log = logging.getLogger(__name__)

# No logging setup needed to see the SQL: DbApiHook.run() (common.sql) logs every
# statement it executes -- including the SQLToolset query tool's -- at INFO under
# "Running statement: ...", unconditionally.


@dag(
    dag_id="task_agent_example",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["claude"],
)
def task_agent_example():
    @task.agent(
        llm_conn_id="anthropic_default",
        toolsets=[
            SQLToolset(
                db_conn_id="dwh_default",
            )
        ],
        # Fail the task rather than let the agent loop indefinitely on a bad prompt.
        usage_limits=UsageLimits(request_limit=10, tool_calls_limit=10),
    )
    def analyze(question: str):
        """Same prompt/XCom inversion as @task.llm, but the agent can call SQLToolset's tools
        (list_tables, get_schema, query, check_query) in a loop before producing a final answer."""
        log.info("Question: %s", question)
        return question

    @task
    def log_answer(answer: str):
        log.info("Answer: %s", answer)

    answer = analyze.override(system_prompt="You are a jazz researcher.")(
        "How many solos are in the database for each artist? Include all artists."
    )
    log_answer(answer)


task_agent_example()
