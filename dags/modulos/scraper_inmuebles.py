import pandas as pd
import re
import time
from DrissionPage import ChromiumPage, ChromiumOptions
import gspread
from datetime import datetime

# 2. Función Principal de Scraping (Totalmente aislada de Airflow)
def ejecutar_scraping():
    # --- RUTAS DE LINUX DENTRO DE DOCKER ---
    filename = ""
    fecha = datetime.today().strftime('%Y-%m-%d')
    tipo_operacion = 'departamento_renta'

    def get_sheet_data(gsheet_name, tab_name):
        gc = gspread.service_account(filename=filename)
        sh = gc.open(gsheet_name)
        worksheet = sh.worksheet(tab_name)
        df = pd.DataFrame(worksheet.get_all_records(numericise_ignore=[4]))
        return df

    def generar_urls_desde_df(df, nombre_pagina, tipo_operacion):
        try:
            url_bruta = df.loc[df['pagina'] == nombre_pagina, tipo_operacion].values[0]
        except IndexError:
            return ["Error: No se encontró la página."]
        if pd.isna(url_bruta) or not str(url_bruta).strip():
            return ["Error: La celda está vacía."]
            
        url_bruta = str(url_bruta)
        if "venta" in tipo_operacion or "remates" in tipo_operacion:
            url_plantilla = url_bruta.replace('1000000', '{min_precio}').replace('2000000', '{max_precio}')
        elif "renta" in tipo_operacion:
            url_plantilla = url_bruta.replace('5000', '{min_precio}').replace('10000', '{max_precio}')
        else:
            url_plantilla = url_bruta

        lista_urls = []
        if "{min_precio}" in url_plantilla:
            if "venta" in tipo_operacion or "remates" in tipo_operacion:
                for i in range(10, 12):
                    min_p = i * 500000
                    max_p = (i + 1) * 500000
                    lista_urls.append(url_plantilla.format(min_precio=min_p, max_precio=max_p))
            elif "renta" in tipo_operacion:
                for i in range(30, 32):
                    min_p = (i * 2000)+1
                    max_p = ((i + 1) * 2000)
                    lista_urls.append(url_plantilla.format(min_precio=min_p, max_precio=max_p))
        else:
            lista_urls.append(url_plantilla)
        return lista_urls

    def scroll_suave(page):
        for _ in range(4):
            page.scroll.down(500) 
            page.wait(0.5) 
        page.scroll.to_bottom()
        page.wait(1)

    def iniciar_navegador_linux():
        co = ChromiumOptions()
        
        co.headless(True)
        co.set_browser_path('/usr/bin/chromium')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-blink-features=AutomationControlled')
        
        # --- NUEVAS TÁCTICAS ANTI-BOTS ---
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
        co.set_argument('--disable-automation')
        co.set_argument('--ignore-certificate-errors')
        
        co.incognito(True)
        return ChromiumPage(co)

    def scrap_store(lista_urls, herramienta, nombre_pagina, tipo_operacion, fecha, page):
        csv_name = f"/opt/airflow/dags/{herramienta}_{nombre_pagina}_{tipo_operacion}_{fecha}.csv"
        print(f"Iniciando scraping... El archivo se guardará como: {csv_name}")

        names_text = []
        urls_article = []
        imgs = []

        for i, url_actual in enumerate(lista_urls):
            print(f"\n--- Procesando URL {i+1} de {len(lista_urls)} ---")
            max_retries = 3
            numero_indice = 1
            
            for attempt in range(max_retries):
                try:
                    time.sleep(3)
                    page.get(url_actual)
                    try:
                        no_list_items = page.ele('.postingsTitle-module__title')
                        resultado = re.search(r'([\d,]+)', no_list_items.text)
                        if resultado:
                            numero_casas = int(resultado.group(1).replace(',', ''))
                            numero_indice = (numero_casas+29) // 30
                    except:
                        pass
                    break 
                except Exception as e:
                    time.sleep(5)

            for l in range(1, numero_indice + 1):
                link = url_actual.replace('pagina-2', f'pagina-{l}')
                for attempt in range(max_retries):
                    try:
                        page.get(link)
                        
                        scroll_suave(page)  
                        page.wait.ele_displayed('.ui-pdp-title', timeout=10) 
                        page.get_screenshot(path=f'/opt/airflow/logs/debug_inmuebles24_{i}_{l}.png')
                        names = page.eles('.postingsList-module__card-container')
                        names_text.extend([name.text for name in names])
                        
                        for articulo in names:
                            enlace = articulo.ele('xpath:.//a', timeout=1) 
                            urls_article.append(enlace.attr('href') if enlace else None)
                            imagen = articulo.ele('xpath:.//img', timeout=1)
                            imgs.append(imagen.attr('src') if imagen else None)
                        break
                    except Exception:
                        time.sleep((attempt + 1) * 5)

        if names_text:
            df2 = pd.DataFrame(names_text, columns=['Text_raw'])
            df2["Url"] = urls_article
            df2["Img"] = imgs
            df2.to_csv(csv_name, encoding='utf-8-sig', index=False)
            print(f"\n✅ Guardado exitoso en: {csv_name}")

    # --- EJECUCIÓN PRINCIPAL ---
    print("Obteniendo URLs de Google Sheets...")
    df_ficha2 = get_sheet_data('ficha_ml_amz', 'real_state_mex')
    urls_venta = generar_urls_desde_df(df_ficha2, 'inmuebles24', tipo_operacion)

    print("Levantando navegador Headless en Ubuntu...")
    page = iniciar_navegador_linux()
    
    try:
        scrap_store(urls_venta, 'Drision', 'inmuebles24', tipo_operacion, fecha, page)
    finally:
        page.quit()