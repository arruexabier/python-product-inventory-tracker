import unittest

from inventory_tracker.compare import compare_snapshots


class CompareSnapshotsTests(unittest.TestCase):
    def setUp(self):
        self.old = [
            {"product_url": "https://shop.test/a", "title": "A", "price_gbp": "10.00", "availability": "In stock"},
            {"product_url": "https://shop.test/b", "title": "B", "price_gbp": "20.00", "availability": "In stock"},
            {"product_url": "https://shop.test/c", "title": "C", "price_gbp": "30.00", "availability": "Out of stock"},
        ]
        self.new = [
            {"product_url": "https://shop.test/a", "title": "A", "price_gbp": "10.00", "availability": "In stock"},
            {"product_url": "https://shop.test/c", "title": "C", "price_gbp": "31.50", "availability": "In stock"},
            {"product_url": "https://shop.test/d", "title": "D", "price_gbp": "40.00", "availability": "In stock"},
        ]

    def test_detects_new_removed_price_and_stock_changes(self):
        changes = compare_snapshots(self.old, self.new, detected_at="test-time")
        kinds = [change["change_type"] for change in changes]
        self.assertEqual(kinds.count("new_product"), 1)
        self.assertEqual(kinds.count("removed_product"), 1)
        self.assertEqual(kinds.count("price_changed"), 1)
        self.assertEqual(kinds.count("availability_changed"), 1)
        self.assertTrue(all(change["detected_at"] == "test-time" for change in changes))

    def test_identical_snapshots_have_no_changes(self):
        self.assertEqual(compare_snapshots(self.old, self.old), [])

    def test_price_comparison_ignores_trailing_zeroes(self):
        old = [{"product_url": "u", "price_gbp": "10.0", "availability": "In stock"}]
        new = [{"product_url": "u", "price_gbp": "10.00", "availability": "In stock"}]
        self.assertEqual(compare_snapshots(old, new), [])

    def test_empty_baseline_marks_all_current_products_as_new(self):
        changes = compare_snapshots([], self.new)
        self.assertEqual(len(changes), len(self.new))
        self.assertTrue(all(change["change_type"] == "new_product" for change in changes))


if __name__ == "__main__":
    unittest.main()
