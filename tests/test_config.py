import unittest
from pathlib import Path

from inventory_tracker.config import load_config


class ConfigTests(unittest.TestCase):
    def test_loads_demo_configuration(self):
        project_root = Path(__file__).resolve().parents[1]
        config = load_config(project_root / "config.json")

        self.assertEqual(config.site_name, "Books to Scrape")
        self.assertTrue(
            config.start_url.startswith("https://")
        )
        self.assertEqual(
            config.selectors["product_card"],
            "article.product_pod",
        )
        self.assertEqual(
            config.selectors["product_price"],
            "p.price_color",
        )

    def test_rejects_missing_configuration(self):
        with self.assertRaisesRegex(
            ValueError,
            "Configuration file not found",
        ):
            load_config("file_that_does_not_exist.json")


if __name__ == "__main__":
    unittest.main()