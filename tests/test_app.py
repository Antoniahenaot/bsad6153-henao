"""Offline app tests: all connection attempts blocked or replaced with mocks."""
import importlib.util
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import psycopg
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pilot', ROOT / 'app/streamlit_app.py')
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)
NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)
SNAPSHOT = (1, '52001', date(2026, 8, 31), NOW)
LATEST = (NOW, 1, date(2026, 8, 31))


def connection(rows=None, role=True):
    conn = MagicMock()
    def execute(sql, params=None):
        result = MagicMock()
        if 'current_user' in sql:
            result.fetchone.return_value = (role,)
        elif 'source_run_id = %s' in sql:
            result.fetchone.return_value = SNAPSHOT
        elif 'SELECT DISTINCT' in sql:
            result.fetchall.return_value = [('block-a',), ('block-b',), (None,)]
        elif 'r.finished_at' in sql:
            result.fetchone.return_value = LATEST
        elif 'GROUP BY p.parcel_id' in sql:
            result.fetchall.return_value = (rows or {}).get('parcels', [('parcel-a', 2), ('parcel-b', 0)])
        elif 'GROUP BY b.construction_type' in sql:
            result.fetchall.return_value = (rows or {}).get('categories', [('Conventional', 2)])
        return result
    conn.execute.side_effect = execute
    return conn


class AppTests(unittest.TestCase):
    def setUp(self):
        app.st.cache_data.clear()
        self.env = patch.dict(os.environ, {'APP_DATABASE_URL': 'offline-test-only', 'FRESHNESS_HOURS': '24'})
        self.env.start()
        self.guard = patch.object(psycopg, 'connect', side_effect=AssertionError('Unexpected connection'))
        self.guard.start()

    def tearDown(self):
        self.guard.stop()
        self.env.stop()

    def test_reader_security_and_close(self):
        conn = connection()
        with patch.object(app.psycopg, 'connect') as connect:
            connect.return_value.__enter__.return_value = conn
            with app.reader() as actual:
                self.assertIs(actual, conn)
            self.assertEqual(connect.call_args.kwargs['connect_timeout'], 10)
            sql = [call.args[0] for call in conn.execute.call_args_list]
            self.assertIn('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY', sql)
            self.assertIn("SET LOCAL statement_timeout = '10s'", sql)
            self.assertTrue(connect.return_value.__exit__.called)

    def test_wrong_role_rejected_before_source_queries(self):
        conn = connection(role=False)
        with patch.object(app.psycopg, 'connect') as connect:
            connect.return_value.__enter__.return_value = conn
            with self.assertRaises(PermissionError):
                with app.reader():
                    self.fail('wrong role accepted')
        self.assertEqual(len(conn.execute.call_args_list), 4)

    def test_missing_reader_never_uses_owner(self):
        with patch.dict(os.environ, {'APP_DATABASE_URL': '', 'DATABASE_URL': 'not-used'}):
            with self.assertRaises(PermissionError):
                with app.reader():
                    self.fail('missing reader accepted')

    def test_filter_parameters_and_shared_scope(self):
        conn = connection()
        malicious = "block' OR true --"
        with patch.object(app, 'reader') as reader:
            reader.return_value.__enter__.return_value = conn
            parcels, categories = app.view_data(1, 'code', malicious)
        for call in conn.execute.call_args_list:
            self.assertNotIn(malicious, call.args[0])
            self.assertEqual(call.args[1], (1, 'code', 'code', 'code', malicious))
        self.assertEqual(sum(n for _, n in parcels), sum(n for _, n in categories))

    def test_cache_separates_snapshot_and_block(self):
        conn = connection()
        with patch.object(app, 'reader') as reader:
            reader.return_value.__enter__.return_value = conn
            app.view_data(1, 'all', None)
            app.view_data(1, 'all', None)
            app.view_data(1, 'code', 'block-a')
            app.view_data(2, 'all', None)
            self.assertEqual(reader.call_count, 3)
        self.assertEqual(app.CACHE_SECONDS, 600)

    def test_invalid_filter_and_inconsistent_totals_rejected(self):
        with self.assertRaises(ValueError):
            app.view_data(1, 'bad', None)
        conn = connection({'categories': [('Conventional', 99)]})
        with patch.object(app, 'reader') as reader:
            reader.return_value.__enter__.return_value = conn
            with self.assertRaises(ValueError):
                app.view_data(1, 'all', None)

    def test_original_run_and_geography(self):
        conn = connection()
        with patch.object(app, 'reader') as reader:
            reader.return_value.__enter__.return_value = conn
            app.context_data()
        self.assertEqual(conn.execute.call_args_list[0].args[1], (app.ORIGINAL_RUN,))
        latest_sql = conn.execute.call_args_list[-1].args[0]
        self.assertIn('github_run_id IS NOT NULL', latest_sql)
        self.assertIn("('manual', 'scheduled')", latest_sql)

    def test_geography_mismatch_rejected(self):
        conn = connection()
        original = conn.execute.side_effect
        def execute(sql, params=None):
            result = original(sql, params)
            if 'source_run_id = %s' in sql:
                result.fetchone.return_value = (1, '17001', date(2026, 8, 31), NOW)
            return result
        conn.execute.side_effect = execute
        with patch.object(app, 'reader') as reader:
            reader.return_value.__enter__.return_value = conn
            with self.assertRaises(ValueError):
                app.context_data()

    def test_failed_queries_are_not_cached(self):
        with patch.object(app, 'reader', side_effect=psycopg.OperationalError('offline')) as reader:
            for _ in range(2):
                with self.assertRaises(psycopg.OperationalError):
                    app.view_data(1, 'all', None)
            self.assertEqual(reader.call_count, 2)

    def test_freshness_boundary_mismatch_future_and_missing(self):
        with patch.object(app.st, 'success') as success, patch.object(app.st, 'warning') as warning, patch.object(app.st, 'caption'):
            app.freshness_banner((NOW - timedelta(hours=24), 1, date(2026, 8, 31)), 1, NOW)
            success.assert_called_once()
            warning.assert_not_called()
            app.freshness_banner((NOW - timedelta(hours=24, seconds=1), 2, date(2026, 8, 31)), 1, NOW)
            self.assertEqual(warning.call_count, 2)
            app.freshness_banner(None, 1, NOW)
            app.freshness_banner((NOW + timedelta(hours=1), 1, date(2026, 8, 31)), 1, NOW)
            self.assertEqual(warning.call_count, 4)

    def test_configured_freshness_threshold_controls_banner(self):
        with patch.dict(os.environ, {'FRESHNESS_HOURS': '6'}), patch.object(app.st, 'success') as success, patch.object(app.st, 'warning') as warning, patch.object(app.st, 'caption'):
            app.freshness_banner((NOW - timedelta(hours=6), 1, date(2026, 8, 31)), 1, NOW)
            success.assert_called_once()
            warning.assert_not_called()
            app.freshness_banner((NOW - timedelta(hours=6, seconds=1), 1, date(2026, 8, 31)), 1, NOW)
            warning.assert_called_once()
            self.assertIn('6-hour operational threshold', warning.call_args.args[0])

    def test_freshness_config_defaults_and_rejects_invalid_values(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(app.freshness_hours(), 24)
        for value in ['', 'invalid', '0', '-1', 'NaN', 'Infinity', '-Infinity']:
            with self.subTest(value=value), patch.dict(os.environ, {'FRESHNESS_HOURS': value}):
                self.assertEqual(app.freshness_hours(), 24)
        with patch.dict(os.environ, {'FRESHNESS_HOURS': '2.5'}):
            self.assertEqual(app.freshness_hours(), 2.5)

    def run_ui(self, conn=None, failure=None, configured=True):
        app.st.cache_data.clear()
        with patch('dotenv.load_dotenv', return_value=False), patch.dict(os.environ, {'APP_DATABASE_URL': 'offline-test-only' if configured else ''}), patch.object(psycopg, 'connect') as connect:
            if failure:
                connect.side_effect = failure
            else:
                connect.return_value.__enter__.return_value = conn or connection()
            at = AppTest.from_file(str(ROOT / 'app/streamlit_app.py'), default_timeout=10).run()
            return at

    def test_ui_views_block_filter_and_no_chatbot(self):
        conn = connection()
        with patch('dotenv.load_dotenv', return_value=False), patch.object(psycopg, 'connect') as connect:
            connect.return_value.__enter__.return_value = conn
            at = AppTest.from_file(str(ROOT / 'app/streamlit_app.py'), default_timeout=10).run()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.metric), 4)
            self.assertEqual(len(at.dataframe), 2)
            self.assertEqual(at.metric[0].value, '2')
            self.assertEqual(len(at.text_input), 0)
            at.selectbox[0].select(('code', 'block-a')).run()
            self.assertFalse(at.exception)
            calls = [c for c in conn.execute.call_args_list if 'GROUP BY' in c.args[0]]
            self.assertTrue(any(c.args[1][1:] == ('code', 'code', 'code', 'block-a') for c in calls))
            at.selectbox[0].select(('missing', None)).run()
            self.assertFalse(at.exception)

    def test_chart_zero_baseline_and_short_metric(self):
        with patch.object(app.st, 'vega_lite_chart', wraps=app.st.vega_lite_chart) as chart:
            at = self.run_ui(connection())
            self.assertFalse(at.exception)
            spec = chart.call_args.kwargs['spec']
            self.assertEqual(spec['encoding']['y']['scale'], {'zero': True, 'domainMin': 0})
            self.assertEqual(at.metric[3].label, 'No building match')
            self.assertIn('vacancy is unknown', at.metric[3].help)
            self.assertFalse(any('Public deployment still requires separate approval' in item.value for item in at.caption))

    def test_ui_connection_error_hides_details(self):
        at = self.run_ui(failure=psycopg.OperationalError('PRIVATE-CONNECTION-DETAIL'))
        self.assertFalse(at.exception)
        self.assertNotIn('PRIVATE-CONNECTION-DETAIL', str(at.error))
        self.assertTrue(at.error)

    def test_ui_wrong_role(self):
        at = self.run_ui(connection(role=False))
        self.assertFalse(at.exception)
        self.assertIn('app_reader', at.error[0].value)

    def test_ui_missing_configuration(self):
        at = self.run_ui(configured=False)
        self.assertFalse(at.exception)
        self.assertTrue(any('not configured' in item.value for item in at.info))

    def test_ui_empty_filter_and_zero_buildings(self):
        for rows, expected in [({'parcels': [], 'categories': []}, 'No parcel'), ({'parcels': [('p', 0)], 'categories': []}, 'no returned building')]:
            at = self.run_ui(connection(rows))
            self.assertFalse(at.exception)
            self.assertTrue(any(expected in item.value for item in at.info))

    def test_ui_missing_snapshot(self):
        conn = connection()
        original = conn.execute.side_effect
        def execute(sql, params=None):
            result = original(sql, params)
            if 'source_run_id = %s' in sql:
                result.fetchone.return_value = None
            return result
        conn.execute.side_effect = execute
        at = self.run_ui(conn)
        self.assertFalse(at.exception)
        self.assertTrue(any('original saved Pasto snapshot is unavailable' in item.value for item in at.info))


if __name__ == '__main__':
    unittest.main()
