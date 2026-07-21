from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# 1. Argumentos por defecto del pipeline
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 7, 19), # Fecha de inicio
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 2. Definición de las funciones en Python (Tus scripts reales irían aquí)
def extract_properties():
    print("Iniciando web scraping de listados de bienes raíces...")
    print("Extracción completada. Datos guardados temporalmente en CSV.")

def upload_to_storage():
    print("Subiendo archivos CSV al bucket de almacenamiento en la nube...")
    print("Carga exitosa.")

def trigger_bronze_layer():
    print("Detonando el procesamiento en la capa Bronze de la plataforma de datos...")

# 3. Creación del DAG
with DAG(
    'real_estate_extraction_pipeline',
    default_args=default_args,
    description='Pipeline de extracción de propiedades y carga a nube',
    schedule_interval=timedelta(days=1), # Se ejecutará todos los días
    catchup=False,
    tags=['extracción', 'bienes_raíces', 'bronze'],
) as dag:

    # 4. Asignación de tareas
    task_extract = PythonOperator(
        task_id='extract_property_listings',
        python_callable=extract_properties,
    )

    task_upload = PythonOperator(
        task_id='upload_csv_to_cloud',
        python_callable=upload_to_storage,
    )

    task_process_bronze = PythonOperator(
        task_id='process_bronze_layer',
        python_callable=trigger_bronze_layer,
    )

    # 5. Definición del orden de ejecución (Dependencias)
    task_extract >> task_upload >> task_process_bronze