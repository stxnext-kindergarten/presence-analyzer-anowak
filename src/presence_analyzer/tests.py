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
TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
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
        main.app.config.update(
            {
                'DATA_CSV': TEST_DATA_CSV,
                'DATA_XML': TEST_DATA_XML
            }
        )
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
        self.assertDictEqual(data[0], {'user_id': 10, 'name': 'Adam P.'})

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
        self.assertDictEqual(
            data,
            {
                'Wed': {
                    'end_work': 58057,
                    'start_work': 33592
                },
                'Sun': {
                    'end_work': 0,
                    'start_work': 0
                },
                'Fri': {
                    'end_work': 0,
                    'start_work': 0
                },
                'Tue': {
                    'end_work': 64792,
                    'start_work': 34745
                },
                'Mon': {
                    'end_work': 0,
                    'start_work': 0
                },
                'Thu': {
                    'end_work': 62631,
                    'start_work': 38926
                },
                'Sat': {
                    'end_work': 0,
                    'start_work': 0}
            }
        )

    def test_prepare_photo_url(self):
        """
        Test preparing correct url for given user_id.
        """
        resp = self.client.get('/api/v1/photo_url/abc')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/photo_url/10')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertEqual(
            data,
            'https://intranet.stxnext.pl/api/images/users/10'
        )

    def test_api_months_view(self):
        """
        Test months listing.
        """
        resp = self.client.get('/api/v1/months')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(data[0], 'September-2013')

    def test_top_5(self):
        """
        Test top 5 emplyees of certein month.
        """
        resp = self.client.get('/api/v1/top_5/Sep-2013')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/top_5/September-9999')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/top_5/September-1')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/top_5/September2013')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/top_5/September-2013')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertEqual(
            data[0],
            [
                11,
                {
                    'total_hours': 32.89,
                    'image': 'https://intranet.stxnext.pl/api/images/users/11',
                    'name': 'Adrian K.'
                }
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
        main.app.config.update(
            {
                'DATA_CSV': TEST_DATA_CSV,
                'DATA_XML': TEST_DATA_XML
            }
        )

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data_from_csv(self):
        """
        Test parsing CSV file.
        """
        data = utils.get_data_from_csv()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(
            data[10][sample_date].keys(),
            ['start', 'end']
        )
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def get_data(self):
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10]['presence'])
        self.assertItemsEqual(
            data[10]['presence'][sample_date].keys(),
            ['start', 'end']
        )
        self.assertEqual(
            data[10]['presence'][sample_date]['start'],
            datetime.time(9, 39, 5)
        )
        self.assertEqual(
            data[10]['name'],
            'Adam P.'
        )

    def test_group_by_weekday(self):
        """
        Test grouping dates by weekdays.
        """
        data = utils.get_data()
        weekdays = utils.group_by_weekday(data[10]['presence'])
        self.assertEqual(weekdays[1][0], 30047)

    def test_seconds_since_midnight(self):
        """
        Test calculating correct amount of seconds since midnight.
        """
        data = utils.get_data()
        time = data[10]['presence'][datetime.date(2013, 9, 10)]['start']
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
        start = data[10]['presence'][datetime.date(2013, 9, 10)]['start']
        end = data[10]['presence'][datetime.date(2013, 9, 10)]['end']
        self.assertEqual(utils.interval(start, end), 30047)

        start = datetime.time(hour=12, minute=0, second=0)
        end = datetime.time(hour=12, minute=0, second=0)
        self.assertEqual(utils.interval(start, end), 0)

    def test_mean(self):
        """
        Test calculating arithmetic mean.
        """
        data = utils.get_data()
        weekdays = utils.group_by_weekday(data[10]['presence'])
        self.assertAlmostEqual(utils.mean(weekdays[1]), 30047)
        self.assertEqual(utils.mean([]), 0)
        self.assertEqual(utils.mean([0]), 0)

    def test_work_hours(self):
        """
        Test calculate starts and ends hours of given user.
        """
        data = utils.get_data()
        start_hours, end_hours = utils.work_hours(data[10]['presence'])
        self.assertListEqual(
            start_hours,
            [[], [34745], [33592], [38926], [], [], []]
        )
        self.assertListEqual(
            end_hours,
            [[], [64792], [58057], [62631], [], [], []]
        )

    def test_cache(self):
        """
        Test caching data in memory for given time.
        """
        utils.CACHE.clear()
        data1 = utils.get_data()
        self.assertDictEqual(
            data1,
            utils.CACHE['get_data']['data']
        )
        data2 = utils.get_dates()
        self.assertEqual(
            data2,
            utils.CACHE['get_dates']['data']
        )
        self.assertEqual(len(utils.CACHE.keys()), 2)
        utils.CACHE.clear()

    def test_total_hours(self):
        """
        Test total workhours of certein month-year by given user.
        """
        data = utils.get_data()
        hours = utils.total_hours(data[10]['presence'], 'September', '2013')
        self.assertEqual(hours, 21.73)
        hours = utils.total_hours(data[11]['presence'], 'September', '2013')
        self.assertEqual(hours, 32.89)


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
