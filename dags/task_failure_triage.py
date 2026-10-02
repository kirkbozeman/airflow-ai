"""
This is an example of utilizing reading a failure log with a downstream LLM task to
assist in triage.
"""

import logging
from datetime import datetime

import requests
from airflow.decorators import dag, task
from airflow.providers.sftp.hooks.sftp import SFTPHook
from airflow.sdk.bases.hook import BaseHook
from airflow.task.trigger_rule import TriggerRule

log = logging.getLogger(__name__)


@dag(
    dag_id="task_failure_triage",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["claude"],
)
def task_failure_triage():

    def _api_auth(connection: str):
        """Get Airflow API base_url and headers"""

        api_conn = BaseHook.get_connection(connection)
        base_url = api_conn.host

        token_resp = requests.post(
            f"{base_url}/auth/token",
            json={"username": api_conn.login, "password": api_conn.password},
        )
        token_resp.raise_for_status()
        headers = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}

        return base_url, headers

    @task(retries=0)
    def sftp_login():
        hook = SFTPHook(ssh_conn_id="sftp_fake")
        hook.list_directory(".")  # forces get_conn() -> a real connection attempt

    @task(trigger_rule=TriggerRule.ALL_FAILED)
    def fetch_failed_log(**context) -> str:

        base_url, headers = _api_auth("airflow_api_default")

        dag_id = context["dag"].dag_id
        run_id = context["dag_run"].run_id

        # sftp_login has retries=0, so it only ever runs once -> always try_number 1
        # additional logic would be needed to deal with tries > 1
        log_resp = requests.get(
            f"{base_url}/api/v2/dags/{dag_id}/dagRuns/{run_id}/taskInstances/sftp_login/logs/1",
            headers=headers,
            params={"accept": "application/json"},
        )
        log_resp.raise_for_status()
        return "\n".join(line["event"] for line in log_resp.json()["content"])

    @task.llm(
        llm_conn_id="anthropic_default",  # anthropic_default is already pinned to Haiku
        system_prompt="You are an SRE triaging a pipeline failure.",
    )
    def explain_failure(log_text: str):
        """Same prompt/XCom inversion as @task.llm elsewhere - the string
        returned here is the prompt sent to the LLM, not the final answer.
        """
        return (
            "This Airflow task failed. Here is its full task log. "
            "Diagnose the real root cause and suggest a fix:\n\n" + log_text
        )

    @task
    def log_explanation(explanation: str):
        log.info("Claude's diagnosis: %s", explanation)

    failed_log = fetch_failed_log()
    sftp_login() >> failed_log
    log_explanation(explain_failure(failed_log))


task_failure_triage()
