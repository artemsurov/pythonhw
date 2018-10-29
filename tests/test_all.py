import datetime
import os
import unittest
from log_analyzer import url_sort, parse_config, is_report_created, search_log, main

class DefaultTestCase(unittest.TestCase):

    default_config = {
        "REPORT_SIZE": 100,
        "REPORT_DIR": "./reports",
        "LOG_DIR": "./log",
        'REGEXP_TEMPLATE': '^(?P<remote_addr>\d+\.\d+\.\d+\.\d+)\s(?P<remote_user>\w+|-)\s+(?P<http_x_real_ip>.+|-)\s+'
                           '\[(?P<time_local>.+)\]\s+"\w+\s(?P<request>.+)HTTP\/\d\.\d"\s(?P<status>\d+)\s'
                           '(?P<body_bytes_sent>\d+)\s"(?P<http_referer>.+)"\s"(?P<http_user_agent>.+)"\s'
                           '"(?P<http_x_forwarded_for>.+)"\s"(?P<http_X_REQUEST_ID>.+)"\s'
                           '"(?P<http_X_RB_USER>.+)"\s(?P<request_time>\d+\.\d+)$',
    }

    def test_url_sort(self):
        data = {'/api/v2/banner/25019354 ':
                    {'count': 1, 'count_perc': 0.1, 'time_sum': 0.39,
                     'time_perc': 0.047743273401243104, 'time_avg': 0.39, 'time_max': 0.39,
                     'time_med': 0.39, 'url': '/api/v2/banner/25019354 '},

                '/api/1/photogenic_banners/list/?server_name=WIN7RB4 ':
                    {'count': 2, 'count_perc': 0.2, 'time_sum': 0.28200000000000003,
                     'time_perc': 0.03452205922859117, 'time_avg': 0.14100000000000001,
                     'time_max': 0.149, 'time_med': 0.149,
                     'url': '/api/1/photogenic_banners/list/?server_name=WIN7RB4 '}
                }
        expected = [{'count': 1, 'count_perc': 0.1, 'time_sum': 0.39,
                     'time_perc': 0.047743273401243104, 'time_avg': 0.39,
                     'time_max': 0.39, 'time_med': 0.39, 'url': '/api/v2/banner/25019354 '}]

        result = url_sort(data, 1)
        self.assertListEqual(result, expected)

    def test_parse_config(self):
        result_conf = {'REPORT_SIZE': 100, 'REPORT_DIR': './reports', 'LOG_DIR': './log',
                       'REGEXP_TEMPLATE': 'fuuuu',
                       'DEBUG': 'True'}

        with open('tests/files/config.txt') as file_config:
            result = parse_config(file_config, DefaultTestCase.default_config)
            self.assertDictEqual(result, result_conf)

    def test_is_report_created(self):
        files = ['report-2017.06.30.html']
        date = datetime.datetime(2017, 6, 30)
        self.assertTrue(is_report_created(files, date))
        files = ['report-2017.06.29.html']
        self.assertFalse(is_report_created(files, date))

    def test_search_log(self):
        # Проверка, что не возьмет лишнего
        files = ['nginx-access-ui.log-20160630.bz']
        finded_log, date, ext = search_log(files)
        self.assertEqual(finded_log, "")
        # Тест,что возьмет недавнюю дату
        files = ['nginx-access-ui.log-20160630.gz', 'nginx-access-ui.log-20160629.gz']
        finded_log, date, ext = search_log(files)
        self.assertEqual(finded_log, "nginx-access-ui.log-20160630.gz")
        # Тест,что возьмет недавнюю дату даже у plain текста
        files = ['nginx-access-ui.log-20160630', 'nginx-access-ui.log-20160629.gz']
        finded_log, date, ext = search_log(files)
        self.assertEqual(finded_log, "nginx-access-ui.log-20160630")

    def test_main(self):
        main(DefaultTestCase.default_config)

    def tearDown(self):
        if os.path.exists("reports/report-2016.06.30.html"):
            os.remove("reports/report-2016.06.30.html")