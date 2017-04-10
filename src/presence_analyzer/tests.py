# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import datetime
import json
import os.path
import unittest

import main
import utils
import views


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """
    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_mean_time_weekday(self):
        """
        Test mean time workhours for each day of given user.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/0')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertListEqual(
            data,
            [
                ['Mon', 0],
                ['Tue', 30047],
                ['Wed', 24465],
                ['Thu', 23705],
                ['Fri', 0],
                ['Sat', 0],
                ['Sun', 0]
            ]
        )

    def test_presence_weekday_view(self):
        """
        Test total presence time for week of given user.
        """
        resp = self.client.get('/api/v1/presence_weekday/0')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertListEqual(
            data,
            [
                ['Weekday', 'Presence (s)'],
                ['Mon', 0],
                ['Tue', 30047],
                ['Wed', 24465],
                ['Thu', 23705],
                ['Fri', 0],
                ['Sat', 0],
                ['Sun', 0]
            ]
        )

    def test_presence_start_end_view(self):
        """
        Test average start and end hours of worktime of given user.
        """
        resp = self.client.get('/api/v1/presence_start_end/0')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertListEqual(
            data,
            [
                ['Mon'],
                ['Tue', 'January 1, 09:39:05', 'January 1, 17:59:52'],
                ['Wed', 'January 1, 09:19:52', 'January 1, 16:07:37'],
                ['Thu', 'January 1, 10:48:46', 'January 1, 17:23:51'],
                ['Fri'],
                ['Sat'],
                ['Sun']
            ]
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_group_by_weekday(self):
        """
        Test grouping dates by weekdays.
        """
        data = utils.get_data()
        weekdays = utils.group_by_weekday(data[10])
        self.assertEqual(weekdays[1][0], 30047)
        weekday_s = utils.group_by_weekday(data[10], seconds=True, start=True)
        self.assertEqual(weekday_s[1][0], 34745)
        weekday_e = utils.group_by_weekday(data[10], seconds=True, end=True)
        self.assertEqual(weekday_e[1][0], 64792)
        self.assertGreater(weekday_e, weekday_s)

    def test_seconds_since_midnight(self):
        """
        Test calculating correct amount of seconds since midnight.
        """
        data = utils.get_data()
        time = data[10][datetime.date(2013, 9, 10)]['start']
        midnight = datetime.time(hour=0, minute=0, second=0)
        midday = datetime.time(hour=12, minute=0, second=0)
        self.assertEqual(utils.seconds_since_midnight(time), 34745)
        self.assertEqual(utils.seconds_since_midnight(midnight), 0)
        self.assertEqual(utils.seconds_since_midnight(midday), 43200)

    def test_interval(self):
        """
        Test calculate intervals in seconds between two time objects.
        """
        data = utils.get_data()
        start = data[10][datetime.date(2013, 9, 10)]['start']
        end = data[10][datetime.date(2013, 9, 10)]['end']
        self.assertEqual(utils.interval(start, end), 30047)

        start = datetime.time(hour=12, minute=0, second=0)
        end = datetime.time(hour=12, minute=0, second=0)
        self.assertEqual(utils.interval(start, end), 0)

    def test_mean(self):
        """
        Test calculating arithmetic mean.
        """
        data = utils.get_data()
        weekdays = utils.group_by_weekday(data[10])
        self.assertAlmostEqual(utils.mean(weekdays[1]), 30047)
        self.assertEqual(utils.mean([]), 0)
        self.assertEqual(utils.mean([0]), 0)


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
