# pythonhw

## Для запуска тестов:
python -m unittest tests/test_all.py

## Для запуска анализатора:
 Необходим файл config.txt, в котором можно переопределить дефолтные переменные:
 * REPORT_SIZE - кол-во строе в итоговом отчете
 * REPORT_DIR - директория куда будут складываться отчеты
 * LOG_DIR - директория с логами
 * REGEXP_TEMPLATE - шаблон регулрного выражения отражающий формат записи строки в логах
 
 Путь до конфига можно указать при запуске с помощью флага --config
 
В папке REPORT_DIR должен лежать файл в формате nginx-access-ui.log-YYYYMMDD c логами
