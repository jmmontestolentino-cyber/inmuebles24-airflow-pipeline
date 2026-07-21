from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# IMPORTACIÓN ESTRATÉGICA: Llamamos al músculo desde la otra carpeta
from modulos.scraper_inmuebles import ejecutar_scraping

# 1. Configuración del Orquestador
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 7, 19),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 2. Estructura del DAG
with DAG(
    'drission_scraper_inmuebles24',
    default_args=default_args,
    description='Scraping automatizado con DrissionPage',
    schedule_interval=timedelta(days=1), # Corre 1 vez al día
    catchup=False,
    tags=['extracción', 'bienes_raíces'],
) as dag:

    # 3. Nodo de ejecución
    tarea_extraccion = PythonOperator(
        task_id='extraer_datos_inmuebles24',
        python_callable=ejecutar_scraping,
    )
    
    tarea_extraccion