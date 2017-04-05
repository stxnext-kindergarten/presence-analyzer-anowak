# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, utils


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
        Test correct format of output data.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/api/v1/mean_time_weekday/0')
        self.assertEqual(resp.status_code, 404)

        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(
            data[0],
            [
                ['Mon', 29934.639175257733],
                ['Tue', 31108.29],
                ['Wed', 30584.429906542056],
                ['Thu', 30602.904761904763],
                ['Fri', 29844.545454545456],
                ['Sat', 0],
                ['Sun', 0]
            ]
        )

    def test_presence_weekday_view(self):
        """
        Test total presence time of given user.
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/api/v1/presence_weekday/0')
        self.assertEqual(resp.status_code, 404)

        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertListEqual(
            data[0],
            [
                ['Weekday', 'Presence (s)'],
                ['Mon', 2903660],
                ['Tue', 3110829],
                ['Wed', 3272534],
                ['Thu', 3213305],
                ['Fri', 2954610],
                ['Sat', 0],
                ['Sun', 0]
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
        self.assertEqual(weekdays[0][0], 30927)

    def test_seconds_since_midnight(self):
        """
        Test calculating correct amount of seconds since midnight.
        """
        data = utils.get_data()
        time = data[10][datetime.date(2012, 7, 5)]['start']
        midnight = datetime.time(hour=0, minute=0, second=0)
        midday = datetime.time(hour=12, minute=0, second=0)
        self.assertEqual(utils.seconds_since_midnight(time), 32917)
        self.assertEqual(utils.seconds_since_midnight(midnight), 0)
        self.assertEqual(utils.seconds_since_midnight(midday), 43200)

    def test_interval(self):
        """
        Test calculate intervals in seconds between two time objects.
        """
        data = utils.get_data()
        start = data[10][datetime.date(2012, 7, 5)]['start']
        end = data[10][datetime.date(2012, 7, 5)]['end']
        self.assertEqual(utils.intervals(start, end), 32907)

        start = datetime.time(hour=12, minute=0, second=0)
        end = datetime.time(hour=12, minute=0, second=0)
        self.assertEqual(utils.interval(start, end), 0)

    def test_mean(self):
        """
        Test calculating arithmetic mean.
        """
        data = utils.get_data()
        weekdays = utils.group_by_weekday(data[10])
        self.assertAlmostEqual(utils.mean(weekdays[0]), 29934)
        self.assertEqual(utils.mean(weekdays[7]), 0)
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
