# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import math
from json import dumps
from functools import wraps
from datetime import datetime

from flask import Response

from main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


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


def get_data():
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


def group_by_weekday(items, *args, **kwargs):
    """
    Groups presence entries by weekday.
    """
    if 'start' in kwargs and kwargs['start'] and \
            'end' in kwargs and kwargs['end']:
        raise KeyError('Conflicting arguments in kwargs!')

    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        if 'seconds' in kwargs:
            if 'start' in kwargs:
                result[date.weekday()].append(seconds_since_midnight(start))
            elif 'end' in kwargs:
                result[date.weekday()].append(seconds_since_midnight(end))
            else:
                raise KeyError('Didn\'t receive \'start\' or \'end\' param.')
        else:
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


def average_hour(items):
    """
    Calculates average hour and returns date string for JS Date object.
    """
    avg_time = round(mean(items))
    avg_m = avg_time / 60
    avg_h = avg_m / 60

    avg_sec = int(math.floor(avg_time % 60))
    if avg_sec < 10:
        avg_sec = '0' + str(avg_sec)

    avg_min = int(math.floor(avg_m % 60))
    if avg_min < 10:
        avg_min = '0' + str(avg_min)

    avg_hour = int(math.floor(avg_h % 24))
    if avg_hour < 10:
        avg_hour = '0' + str(avg_hour)

    return "January 1, 2013 {}:{}:{}".format(avg_hour, avg_min, avg_sec)
