#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from collections import OrderedDict
import copy

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def clean(self, value):
        clean_value = self.to_python(value)
        self.validate(clean_value)

    def to_python(self, value):
        return value

    def validate(self, value):
        if self.required is True and value is None:
            raise Exception("Value requred!")
        elif self.nullable is False and value is None:
            raise Exception("Value shouldn't be empty")


class CharField(Field):

    def to_python(self, value):
        return str(value)


class ArgumentsField(Field):

    def __init__(self, class_name, **kwargs):
        self.class_name = class_name
        super(ArgumentsField,self).__init__(**kwargs)

    @classmethod
    def register_method(cls, *clasess):
        cls.arguments_clasess = clasess

    def validate(self, value):
        method_name


class EmailField(CharField):
    def validate(self, value):
        if "@" not in value:
            raise Exception("EmailField must contain '@' ")


class PhoneField(Field):
    def to_python(self, value):
        if value is None:
            return ""
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, str):
            return value
        else:
            raise Exception("Value is not string and not integer")

    def validate(self, value):
        if value == "":
            return
        elif len(value) != 11 and value[0] != '7':
            raise Exception('PhoneField value is < 11')


class DateField(Field):

    def to_python(self, value):
        return datetime.datetime.strptime(value, "%Y%:%m:%d").date()


class BirthDayField(DateField):

    def validate(self, value):
        if value > datetime.timedelta(days=365 * 70):
            raise Exception("Atention! Tooo oldd")


class GenderField(Field):
    def to_python(self, value):
        return int(value)

    def validate(self, value):
        if value not in GENDERS:
            raise Exception("GenderField must contain only 3 genders")


class ClientIDsField(Field):

    def validate(self, value):

        if not isinstance(value, list):
            raise Exception('ClientIDsField type error')

        elif len(value) == 0:
            raise Exception('ClientIDsField is required')

        elif not all(isinstance(i, int) for i in value):
            raise Exception('ClientIDsField elements of list must be integer')


class Meta(type): #todo  переделать, чтобы работал с классами internal
    def __new__(mcs, name, bases, attrs):
        current_fields = []
        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                current_fields.append((key, value))
                attrs.pop(key)
        attrs['declared_fields'] = OrderedDict(current_fields)

        new_class = super(Meta, mcs).__new__(mcs, name, bases, attrs)

        return new_class


class Base(object):
    def __init__(self, data):
        self.data = data
        self.fields = copy.deepcopy(self.declared_field)

    def is_valid(self):
        for name, class_field in self.fields.items():
            value = self.data.get(name)
            if isinstance(class_field, ArgumentsField):
                class_field.register_method(OnlineScoreRequest, ClientsInterestsRequest)

            else:
                class_field.clean(value)
            self.cleaned_data[name] = value


class Request(Base, metaclass=Meta):
    pass


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    class Internal(object): #todo использовать класс Validate, как отметку для метакласса, что эти поля нужно валидировать отдельно
        name = 'clients_interests'


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    class Internal(object):
        name = 'online_score'


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


"""
работаем с этой функцией
надо добавить валидацию поленй, как у джанги forms
MethodRequest(request) - на выходе получаю валидный реквест
во время вызова MethodRequest запускается мета класс который запустит
проверки для OnlineScoreRequest и ClientsInterestsRequest
потом валидный request передается check_auth
и считается скор с помощью scoring.py
"""


def method_handler(request, ctx, store):
    response, code = None, None
    method = MethodRequest(request)
    if method.is_valid():
        method.cleaned_data

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
