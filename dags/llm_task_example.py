"""This is an example of utilizing task.llm with Anthropic API, specifically the following:

1. Ask a question, receive an unstructured text response.
2. Ask a question, receive a structured response.

Note that system_prompt can be passed per task. It can also be defined along with other parameters
directly in the decorator.
"""

import logging
from datetime import datetime

from airflow.decorators import dag, task
from pydantic import BaseModel

log = logging.getLogger(__name__)


class Results(BaseModel):
    first_name: str
    last_name: str
    dob_year: int
    bio: str


@dag(
    dag_id="llm_task_example",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["claude"],
)
def llm_task_example():
    @task.llm(
        llm_conn_id="anthropic_default",
    )
    def ask_unstructured(question: str):
        """The string returned by @task.llm is used as the prompt sent to the LLM, rather than being
        pushed directly to XCom like a normal TaskFlow return value.

        The LLM's response is then stored in XCom as `return_value`, so downstream tasks receive the
        response, not the original prompt.

        If a downstream task also needs the original question, it must be pushed to XCom explicitly
        before returning.
        """
        log.info("Question: %s", question)
        return question

    @task
    def log_answer(answer: str):
        """Explicitly log the response."""
        log.info("Answer: %s", answer)

    @task.llm(
        llm_conn_id="anthropic_default",
        output_type=list[Results],
    )
    def ask_structured(question: str):
        """Same prompt/XCom inversion as ask_unstructured, but the reply is forced into
        `output_type` (list[Results]) instead of returned as raw text.

        There's no explicit mapping telling the model which words go in which field. It infers that
        from the prompt content plus the schema itself — field names (first_name, bio, ...), their
        types, and any Field(description=...) you add. Vague field names could cause problems, so be
        clear when defining them.
        """
        log.info("Question: %s", question)
        return question

    @task
    def log_results(results: list[Results]):
        for result in results:
            log.info(
                "%s %s (b. %d): %s",
                result.first_name,
                result.last_name,
                result.dob_year,
                result.bio,
            )

    # below run in parallel, just an example so it's ok

    answer1 = ask_unstructured.override(system_prompt="You are a pensive, dramatic Victorian.")(
        "Do you remember the 21st night of September?"
    )
    log_answer(answer1)

    answer2 = ask_structured.override(system_prompt="You are pretentious but concise.")(
        "Give brief one-sentence biographies of 5 famous historical figures born on September 21st."
    )
    log_results(answer2)


llm_task_example()
