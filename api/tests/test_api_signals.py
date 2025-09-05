import unittest
from typing import Any, Dict, List

from fastapi.testclient import TestClient
from api.server_full import APP


class SignalsApiSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(APP)

    def test_signals_shape_and_enrichment(self):
        """
        /signals vrací list objektů s kontraktem:
        - type, hs6
        - partner_iso3 nebo partner_name
        - exportní signály obsahují klíče delta_pct/current_usd (hodnoty mohou být None)
        """
        r = self.client.get("/signals")
        self.assertEqual(r.status_code, 200)
        data: List[Dict[str, Any]] = r.json()
        self.assertIsInstance(data, list)
        if not data:
            self.skipTest("No signals in fixture")

        s0 = data[0]
        # minimální shape
        for k in ["type", "hs6", "label"]:
            self.assertIn(k, s0)

        # partner: akceptuj name nebo iso3
        has_partner_field = ("partner_name" in s0) or ("partner_iso3" in s0)
        self.assertTrue(has_partner_field, "Expected partner_name or partner_iso3 in signal")

        # exportní signály – klíče pro čísla existují
        export_signals = [s for s in data if s.get("type") == "YoY_export_change"]
        self.assertTrue(export_signals, "Expected at least one YoY_export_change signal")
        for s in export_signals:
            self.assertIn("delta_pct", s)
            self.assertIn("current_usd", s)
            # Pokud jsou vyplněny, musí být numerické
            if s.get("delta_pct") is not None:
                self.assertIsInstance(s["delta_pct"], (int, float))
            if s.get("current_usd") is not None:
                self.assertIsInstance(s["current_usd"], (int, float))

    def test_yoy_export_test_endpoint(self):
        """
        /__tests/signals_yoy_export je volitelný (404 povoleno).
        Když je dostupný, má vrátit report se smysluplnými klíči.
        """
        r = self.client.get("/__tests/signals_yoy_export")
        self.assertIn(r.status_code, (200, 404))
        if r.status_code == 404:
            self.skipTest("Dev test endpoint not available or signals file missing")

        report = r.json()
        for k in ["ok", "total_yoy_export_signals", "with_values", "examples"]:
            self.assertIn(k, report)
        self.assertIsInstance(report["ok"], bool)
        self.assertIsInstance(report["total_yoy_export_signals"], int)
        self.assertIsInstance(report["with_values"], int)
        self.assertIsInstance(report["examples"], list)

    def test_partner_share_yoy_shape_and_values(self):
        """
        YoY_partner_share_change:
        - má klíče current_share a delta_pp
        - aspoň jeden záznam má čísla (pokud typ existuje v payloadu)
        """
        r = self.client.get("/signals")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIsInstance(data, list)

        partner_share_signals = [s for s in data if s.get("type") == "YoY_partner_share_change"]
        if not partner_share_signals:
            self.skipTest("No YoY_partner_share_change signals in fixture")

        for s in partner_share_signals:
            self.assertIn("current_share", s)
            self.assertIn("delta_pp", s)
            if s.get("current_share") is not None:
                self.assertIsInstance(s["current_share"], (int, float))
            if s.get("delta_pp") is not None:
                self.assertIsInstance(s["delta_pp"], (int, float))


if __name__ == "__main__":
    unittest.main()