from datetime import datetime, timedelta
from airflow import DAG
from docker.types import Mount
from airflow.operators.python_operators import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.docker import DockerOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    "email_on_retry": False
    
}


def run_elt_script():
    script_path = "/opt/airflow/elt/elt_script.py"
    result = subprocess.run("python", script_path, capture_output= True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Script failed with error: {result.stderr}")
    else:
        print(result.stdout)
        

dag = DAG(
    'elt_and_dbt',
    default_args=default_args,
    description='An ELT workflow with dbt',
    start_date=datetime(2024, 4, 26),
    catchup=False
)

t1 = PythonOperator(
    task_id="run_elt_script",
    python_callable=run_elt_script,
    dag=dag
)

t2 = DockerOperator(
    task_id="dbt_run",
    image='ghcr.io/dbt-labs/dbt-postgres:1.4.7',
    command=[
        "run",
        "--profiles-dir",
        "/root",
        "--project-dir",
        "/dbt"
    ]
    auto_remove=True,
    docker_url="unix://var/run/docker.sock",
    network_mode="bridge",
    mounts=[
        Mount(source='/Documents/DE_project/elt/custom_postgres', target='/dbt', type='bind'),
        Mount(source='C:/Users/Bojan/.dbt', target='/root', type='bind')
    ]
    dag=dag

)

t1 >> t2 # the order at which the tasks are going to run