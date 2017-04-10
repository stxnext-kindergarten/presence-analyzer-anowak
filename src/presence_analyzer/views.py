# -*- coding: utf-8 -*-
"""
Defines views.
"""
import os
import calendar
from flask import redirect, abort, json

from main import app
from utils import jsonify, get_data, mean, \
    group_by_weekday, average_hour

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/static/presence_weekday.html')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns daily timespan working hours of given user.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    start_times = group_by_weekday(data[user_id], seconds=True, start=True)
    end_times = group_by_weekday(data[user_id], seconds=True, end=True)

    result = []
    for i in xrange(5):  # 5 days of week
        avg_start = average_hour(start_times[i])
        avg_end = average_hour(end_times[i])
        result.append(
            [calendar.day_abbr[i], avg_start, avg_end]
        )
    return result


@app.route('/api/v1/resp', methods=['GET'])
@jsonify
def test_resp_view():
    TEST_DATA_CSV = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'runtime',
        'data',
        'test_data.csv'
    )
    app.config.update({'DATA_CSV': TEST_DATA_CSV})
    client = app.test_client()
    resp = client.get('/api/v1/users')
    return json.loads(resp.data)
