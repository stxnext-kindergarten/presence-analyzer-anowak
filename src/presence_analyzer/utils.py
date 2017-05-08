# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""
from __future__ import division

import calendar
import csv

from datetime import datetime
from functools import wraps
from json import dumps
from threading import Lock
from time import time
from xml.etree import ElementTree

from flask import Response

from main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name

CACHE = {}
LOCK = Lock()


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def cache(period):
    """
    Caching decorator. Refreshes cached data if time expired.

    Cache dict structure:
    CACHE = {
        function.__name__: {
            'last_caching':  1493018167.846858
            'data': function(*args, **kwargs)
        },
    }
    """
    def decorating_wrapper(function):
        def caching_wrapper(*args, **kwargs):
            global CACHE
            func_name = function.__name__
            try:
                if (time() - CACHE[func_name]['last_caching']) > period:
                    CACHE[func_name] = {
                        'data': function(*args, **kwargs),
                        'last_caching': time()
                    }
            except KeyError:
                with LOCK:
                    CACHE.setdefault(func_name, {})['data'] = function(
                        *args,
                        **kwargs
                    )
                    CACHE.setdefault(func_name, {})['last_caching'] = time()
            return CACHE[func_name]['data']
        return caching_wrapper
    return decorating_wrapper


@cache(600)
def get_data():
    """
    Extracts data from XML file, tries to match user_id from
    CSV file and binds it.

    It creates structure like this:
    data = {
        user_id = {
            'name': 'Jan K.',
            'presence': {
                datetime.date(2013, 10, 1): {
                    'start': datetime.time(9, 0, 0),
                    'end': datetime.time(17, 30, 0),
                },
                datetime.date(2013, 10, 2): {
                    'start': datetime.time(8, 30, 0),
                    'end': datetime.time(16, 45, 0),
                }
            }
        }
    }
    """
    data = {}
    csv_data = get_data_from_csv()
    tree = ElementTree.parse(app.config['DATA_XML'])
    children = tree.getroot().getchildren()
    users = filter(lambda x: x.tag == 'users', children)
    if not len(users):
        raise KeyError('No users data in XML file.')

    for user in users[0]:
        user_id = int(user.attrib['id'])
        name = user.find('name').text
        try:
            presence = csv_data[user_id]
        except KeyError:
            presence = []
        data.setdefault(user_id, {})['name'] = name
        data.setdefault(user_id, {})['presence'] = presence
    return data


def get_data_from_csv():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue
            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}
    return data


@cache(600)
def get_dates():
    """
    Extracts months and years from CSV for dropdown menu.
    """
    months = []
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue
            try:
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                value = '{}-{}'.format(
                    date.year,
                    calendar.month_name[date.month]
                )
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            if value not in months:
                months.append(value)
    return list(reversed(months))


def get_server_config():
    """
    Extracts server config from XML file.
    """
    tree = ElementTree.parse(app.config['DATA_XML'])
    children = tree.getroot().getchildren()
    config = filter(lambda x: x.tag == 'server', children)
    if not len(config):
        raise KeyError('No server info in XML file.')

    return {
        'host': config[0].find('host').text,
        'port': config[0].find('port').text,
        'protocol': config[0].find('protocol').text
    }


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[] for i in xrange(7)]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates interval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def work_hours(items):
    """
    Returns tuple of start and end hours.
    """
    start_hours = [[] for i in xrange(7)]
    end_hours = [[] for i in xrange(7)]
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        start_hours[date.weekday()].append(seconds_since_midnight(start))
        end_hours[date.weekday()].append(seconds_since_midnight(end))
    return (start_hours, end_hours)


def total_hours(items, month, year):
    """
    Returns total working hours.
    """
    if not items:
        return 0

    year = int(year)
    seconds = 0
    for date in items:
        if calendar.month_name[date.month] == month and date.year == year:
            seconds += interval(items[date]['start'], items[date]['end'])
    return round(seconds / 3600, 2)
