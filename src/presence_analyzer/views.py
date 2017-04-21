# -*- coding: utf-8 -*-
"""
Defines views.
"""
from calendar import day_abbr
from collections import OrderedDict

from flask import abort, redirect, make_response
from flask_mako import render_template
from mako.exceptions import TopLevelLookupException

from main import app
from utils import (
    get_data,
    get_server_config,
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
    return redirect('presence_weekday.html')


@app.route('/<string:template>', methods=['GET'])
def serve_template(template):
    """
    Serves appropriate template by param.
    """
    try:
        return render_template(template, templates=TEMPLATES, current=template)
    except TopLevelLookupException:
        return make_response('page not fond', 404)


@app.route('/api/v1/photo_url/<int:user_id>', methods=['GET'])
@jsonify
def prepare_photo_url(user_id):
    """
    Returns url for intranet api in order to get photo of given user.
    """
    conf = get_server_config()
    return '{}://{}/api/images/users/{}'.format(
        conf['protocol'],
        conf['host'],
        str(user_id)
    )


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': data[i]['name']}
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

    if not len(data[user_id]['presence']):
        return []

    weekdays = group_by_weekday(data[user_id]['presence'])
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

    if not len(data[user_id]['presence']):
        return []

    weekdays = group_by_weekday(data[user_id]['presence'])
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

    if not len(data[user_id]['presence']):
        return {}

    start_times, end_times = work_hours(data[user_id]['presence'])

    work_days = OrderedDict()
    for i in xrange(7):  # 7 days a week
        work_days[day_abbr[i]] = {
            'start_work': int(mean(start_times[i])),
            'end_work': int(mean(end_times[i]))
        }
    return work_days
