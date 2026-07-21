FROM apache/airflow:2.9.2

USER root
# Instalamos las herramientas base y el navegador Chromium
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     build-essential \
     chromium \
     chromium-driver \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow
# Instalamos las librerías de datos, orquestación y web scraping
RUN pip install --no-cache-dir \
    "apache-airflow==2.9.2" \
    apache-airflow-providers-databricks \
    databricks-sql-connector \
    apache-airflow-providers-apache-kafka \
    confluent-kafka \
    pandas \
    pyarrow \
    DrissionPage \
    gspread \
    openpyxl \
    requests \
    numpy