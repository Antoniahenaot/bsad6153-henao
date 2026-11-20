"""Offline checks only: no credentials, API requests, or database connections."""

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
import sync


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.parcels = [
            {"object_id": 2, "codigo": "b", "geometry": {"rings": [[[1.0, 2.0]]] }},
            {"object_id": 1, "codigo": "a", "geometry": {"rings": [[[3, 4]]] }},
        ]
        self.buildings = [{"object_id": 3, "terreno_codigo": "a"}]

    def test_order_and_integral_geometry_representations_do_not_duplicate(self):
        changed = copy.deepcopy(list(reversed(self.parcels)))
        changed[1]["geometry"]["rings"] = [[[1, 2]]]
        self.assertEqual(sync.fingerprint(self.parcels, self.buildings),
                         sync.fingerprint(changed, self.buildings))

    def test_attribute_geometry_membership_and_release_changes_are_detected(self):
        original = sync.fingerprint(self.parcels, self.buildings)
        changed = copy.deepcopy(self.parcels)
        changed[0]["codigo"] = "changed"
        self.assertNotEqual(original, sync.fingerprint(changed, self.buildings))
        changed = copy.deepcopy(self.parcels)
        changed[0]["geometry"]["rings"][0][0][0] = 7
        self.assertNotEqual(original, sync.fingerprint(changed, self.buildings))
        self.assertNotEqual(original, sync.fingerprint(self.parcels[:1], self.buildings))
        with patch.object(sync.fetch, "RELEASE", "2026-09-30"):
            self.assertNotEqual(original, sync.fingerprint(self.parcels, self.buildings))


class FetchTests(unittest.TestCase):
    @patch.object(sync.fetch.time, "sleep")
    def test_existing_page_retries_429_and_503_then_succeeds(self, sleep):
        session = Mock()
        limited = Mock(status_code=429, headers={"Retry-After": "2"})
        unavailable = Mock(status_code=503, headers={})
        good = Mock(status_code=200, content=b'{}')
        good.json.return_value = {"features": []}
        session.get.side_effect = [limited, unavailable, good]
        sync.fetch.request_page(session, 7, {})
        self.assertEqual(session.get.call_count, 3)
        self.assertIn(unittest.mock.call(2), sleep.call_args_list)

    @patch.object(sync.fetch.time, "sleep")
    def test_retry_limit_stops_persistent_failure(self, sleep):
        session = Mock()
        session.get.return_value = Mock(status_code=503, headers={})
        with self.assertRaises(sync.fetch.FetchError):
            sync.fetch.request_page(session, 7, {})
        self.assertEqual(session.get.call_count, sync.fetch.MAX_ATTEMPTS)

    def test_metadata_change_aborts_before_file_validation(self):
        with patch.object(sync, "metadata", side_effect=[{"v": 1}, {}, {"v": 2}, {}]), \
             patch.object(sync.fetch, "fetch", return_value={}), \
             patch.object(sync.load, "read_layer") as reader:
            with self.assertRaises(sync.fetch.FetchError):
                sync.download()
            reader.assert_not_called()

    def test_request_budget_prevents_network_request(self):
        with sync.BoundedSession() as session:
            session.requests_left = 0
            with patch.object(sync.requests.Session, "get") as request:
                with self.assertRaises(sync.fetch.FetchError):
                    session.get("https://example.invalid")
                request.assert_not_called()


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.parcels = [{"object_id": 1, "codigo": "a", "geometry": {"rings": [[[1, 2]]]}}]
        self.buildings = [{"object_id": 2, "terreno_codigo": "a", "geometry": {"rings": [[[3, 4]]]}}]
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.cursor.rowcount = 1

    def test_existing_snapshot_is_reused_without_any_source_upserts(self):
        self.cursor.fetchall.return_value = [(9,)]
        with patch.object(sync, "read_rows", side_effect=[self.parcels, self.buildings] * 2), \
             patch.object(sync.load, "upsert") as upsert:
            total, created = sync.store(self.connection, "test", None,
                                        self.parcels, self.buildings, (1, 1, 1, 0))
        self.assertEqual((total, created), (2, False))
        upsert.assert_not_called()
        self.connection.transaction.return_value.__exit__.assert_called_once_with(None, None, None)

    def test_snapshot_comparison_requests_binary_database_results(self):
        self.cursor.fetchall.return_value = [(9,)]
        with patch.object(sync, "read_rows", side_effect=[self.parcels, self.buildings] * 2):
            sync.store(self.connection, "test", None,
                       self.parcels, self.buildings, (1, 1, 1, 0))
        self.connection.cursor.assert_called_once_with(binary=True)

    def test_new_snapshot_uses_upserts_in_parent_first_order(self):
        self.cursor.fetchall.return_value = []
        self.cursor.fetchone.side_effect = [None, (10,)]
        with patch.object(sync, "read_rows", side_effect=[self.parcels, self.buildings]), \
             patch.object(sync.load, "upsert") as upsert:
            total, created = sync.store(self.connection, "test", None,
                                        self.parcels, self.buildings, (1, 1, 1, 0))
        self.assertEqual((total, created), (2, True))
        self.assertEqual([call.args[1] for call in upsert.call_args_list],
                         ["cadastral_snapshots", "parcels", "buildings"])

    def test_failed_verification_exits_transaction_with_exception(self):
        self.cursor.fetchall.return_value = [(9,)]
        with patch.object(sync, "read_rows", side_effect=[self.parcels, self.buildings, [], []]):
            with self.assertRaises(ValueError):
                sync.store(self.connection, "test", None,
                           self.parcels, self.buildings, (1, 1, 1, 0))
        exit_args = self.connection.transaction.return_value.__exit__.call_args.args
        self.assertIs(exit_args[0], ValueError)
        statements = [str(call.args[0]) for call in self.cursor.execute.call_args_list]
        self.assertFalse(any("status = 'success'" in statement for statement in statements))


if __name__ == "__main__":
    unittest.main()
