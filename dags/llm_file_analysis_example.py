"""This is an example of utilizing task.llm_file_analysis with Anthropic API to analyze a CSV.

The dataset is downloaded from Kaggle at run time (via kagglehub, Kaggle's official Python client)
and is not stored in the repo:
https://www.kaggle.com/datasets/harishyadav0506/impact-of-social-media-on-life
"""

import logging
from datetime import datetime

from airflow.decorators import dag, task

log = logging.getLogger(__name__)

KAGGLE_DATASET = "harishyadav0506/impact-of-social-media-on-life"


@dag(
    dag_id="llm_file_analysis_example",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["claude"],
)
def llm_file_analysis_example():
    @task
    def download_dataset() -> str:
        """Download the dataset (cached locally by kagglehub) and return the CSV path.

        Public datasets download anonymously. The path is local to the worker, so this task and the
        analysis task must run on the same machine (true for this single-worker setup).
        """
        import kagglehub

        dir_path = kagglehub.dataset_download(KAGGLE_DATASET)
        csv_path = f"{dir_path}/Social_media_impact_on_life.csv"
        log.info("Downloaded to %s", csv_path)
        return csv_path

    @task.llm_file_analysis(
        llm_conn_id="anthropic_default",
        # CSVs are not sent whole: the LLM sees the header plus the first `sample_rows` rows (not
        # random). Rendered text is also capped at ~10k chars (~85 rows here), so values above that
        # have no effect. Findings reflect a small slice of the 4,500 rows.
        # So for real world use, there may be more work to do to wrangle the data.
        sample_rows=100,
    )
    def analyze(question: str):
        """The returned string is the prompt; the file contents are attached by the operator."""
        log.info("Question: %s", question)
        return question

    @task
    def log_analysis(analysis: str):
        log.info("Analysis:\n%s", analysis)

    csv_path = download_dataset()
    analysis = analyze.override(
        file_path=csv_path,
        system_prompt="You are a cautious data analyst. Ground every claim in the data provided "
        "and note that findings are correlational and based on a sample. "
        "Make sure to state the exact number of rows you saw and not just the "
        "total number of records (e.g. 'looking at X number of Y records')",
    )("What insights does this data provide on how social media affects quality of life?")
    log_analysis(analysis)


llm_file_analysis_example()
