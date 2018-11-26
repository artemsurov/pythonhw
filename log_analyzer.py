#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import argparse
import configparser
import gzip
import json
import re
import os
import logging
import copy
import datetime
from collections import namedtuple
from string import Template
import pathlib

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    'REGEXP_TEMPLATE': '^(?P<remote_addr>\d+\.\d+\.\d+\.\d+)\s(?P<remote_user>\w+|-)\s+(?P<http_x_real_ip>.+|-)\s+'
                       '\[(?P<time_local>.+)\]\s+"\w+\s(?P<request>.+)HTTP\/\d\.\d"\s(?P<status>\d+)\s'
                       '(?P<body_bytes_sent>\d+)\s"(?P<http_referer>.+)"\s"(?P<http_user_agent>.+)"\s'
                       '"(?P<http_x_forwarded_for>.+)"\s"(?P<http_X_REQUEST_ID>.+)"\s'
                       '"(?P<http_X_RB_USER>.+)"\s(?P<request_time>\d+\.\d+)$',
}


def parse_args():
    parser = argparse.ArgumentParser(description='Process log files')
    parser.add_argument('--config', help='Path to config', default="config.ini", type=open)
    args = parser.parse_args()
    return args


def parse_config(config_file, old_config):
    updated_config = copy.deepcopy(old_config)
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read_file(config_file)
    updated_config.update(config['DEFAULT'])
    return updated_config


def init_logging(config):
    loglevel = logging.DEBUG if bool(config.get("DEBUG", False)) else logging.INFO
    logfile = config.get('LOGGING_FILE', None)
    logging.basicConfig(filename=logfile, level=loglevel,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def search_not_processed_log(log_dir):
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    path = os.path.abspath(log_dir)
    files = os.listdir(path)
    file_name_for_processing = namedtuple('FileName', 'path date ext')
    re_pattern = "nginx-access-ui.log" + "-(?P<data>\d{8})(\.(?P<ext>gz))?$"
    recent_date = datetime.datetime(1, 1, 1)
    extension = ""
    tmp_file_name = ""
    logging.debug(f"Files in LOG_DIR {files}\n")
    for file in files:
        matched_date = re.fullmatch(re_pattern, file)
        if matched_date:
            date = datetime.datetime.strptime(matched_date.group('data'), "%Y%m%d")
            if recent_date < date:
                tmp_file_name = file
                recent_date = date
                extension = matched_date.group('ext')
    if not tmp_file_name:
        return file_name_for_processing(str(pathlib.Path(path) / tmp_file_name), recent_date, extension)


def is_report_created(report_dir, file):
    data = file.date.strftime("%Y.%m.%d")
    file_report = f'report-{data}.html'
    if os.path.exists(pathlib.Path(report_dir) / file_report):
        logging.info(f"Logs file {file} already been processing")
        return True
    return False


def aggregate_data(parser):
    big_dic = {}
    general_request_count = 0
    general_request_time = 0

    for data in parser:
        request = data['request']
        request_time = float(data['request_time'])

        if request not in big_dic:
            big_dic[request] = {'count': 0, 'count_perc': 0, 'time_sum': 0, 'time_perc': 0,
                                'time_avg': 0, 'time_max': 0, 'time_med': 0, 'time_list': [], 'url': request}

        big_dic[request]['count'] += 1
        big_dic[request]['time_sum'] += request_time

        if request_time > big_dic[request]['time_max']:
            big_dic[request]['time_max'] = request_time

        big_dic[request]['time_list'].append(request_time)

        general_request_count += 1
        general_request_time += request_time

    for req in big_dic.values():
        sum = 0
        for time in req['time_list']:
            sum = sum + time
        avg = sum / len(req['time_list'])
        req['time_avg'] = avg

        req['time_list'].sort()
        req['time_med'] = req['time_list'][len(req['time_list']) // 2]

        req['time_perc'] = req['time_sum'] / (general_request_time / 100)
        req['count_perc'] = req['count'] / (general_request_count / 100)
        del req['time_list']
        logging.debug(req)
    return big_dic


def logs_parser(config, log):
    pattern = re.compile(config['REGEXP_TEMPLATE'])
    line_count = 0
    error_line = 0
    func_open = gzip.open if log.ext == "gz" else open
    with func_open(log.path, 'rt') as file:
        for line in file:
            line_count += 1
            splited_data = pattern.match(line)
            if not splited_data:
                logging.error(f"Line NOT MATCHED: {line}")
                error_line += 1
            else:
                yield splited_data.groupdict()

        if error_line / (line_count / 100) > 30:
            raise RuntimeError("To much line matched with error")


def generate_report(config, data, log):
    size = config['REPORT_SIZE']
    report_dir = config["REPORT_DIR"]
    sorted_data = url_sort(data, size)
    data = log.date.strftime("%Y.%m.%d")
    with open('report.html', 'r') as report:
        text = report.read()
        s = Template(text)
        tj1 = json.dumps(sorted_data)
        outdata = s.safe_substitute(table_json=tj1)
        with open(f'{report_dir}/report-{data}.html', 'wt') as newreport:
            newreport.writelines(outdata)


def url_sort(data: dict, size: int) -> list:
    array = sorted(data.values(), key=lambda ip: ip['time_sum'], reverse=True)
    return array[:size]


def main(conf):
    log_dir = conf['LOG_DIR']
    log_file = search_not_processed_log(log_dir)
    if not log_file:
        logging.info(f"Logs not found in {log_dir}")
        return 0
    created = is_report_created(conf["REPORT_DIR"], log_file)
    if created:
        logging.info("Finished")
        return 0
    parser = logs_parser(conf, log_file)
    data = aggregate_data(parser)
    generate_report(conf, data, log_file)


if __name__ == "__main__":
    args = parse_args()
    updated_config = parse_config(args.config, config)
    init_logging(updated_config)
    try:
        main(updated_config)
    except Exception:
        logging.exception("An Exception occurred!")
