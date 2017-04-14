# -*- coding: utf-8 -*-
"""
Defines views.
"""
from calendar import day_abbr
from collections import OrderedDict

from flask import abort, render_template

from main import app
from utils import (
    get_data,
    group_by_weekday,
    jsonify,
    mean,
    work_hours
)

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name

TEMPLATES = [
    ('presence_weekday.html', 'Presence weekday'),
    ('mean_time_weekday.html', 'Mean time weekday'),
    ('presence_start_end.html', 'Presence start-end')
]


@app.route('/', methods=['GET'])
def mainpage():
    """
    Redirects to front page.
    """
    context = {
        'templates': TEMPLATES,
        'current': TEMPLATES[0][0]
    }

    return render_template(
        TEMPLATES[0][0],
        context=context
    )


@app.route('/<template>', methods=['GET'])
def serve_template(template):
    """
    Serves appropriate template by param.
    """
    context = {
        'templates': TEMPLATES,
        'current': template
    }

    return render_template(
        template,
        context=context
    )


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
        (day_abbr[weekday], mean(intervals))
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
        (day_abbr[weekday], sum(intervals))
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

    start_times, end_times = work_hours(data[user_id])

    work_days = OrderedDict()
    for i in xrange(7):  # 7 days a week
        work_days[day_abbr[i]] = {
            'start_work': int(mean(start_times[i])),
            'end_work': int(mean(end_times[i]))
        }
    return work_days
