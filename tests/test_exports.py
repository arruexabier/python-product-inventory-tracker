import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import load_workbook

from inventory_tracker.cli import write_xlsx


class ExcelExportTests(unittest.TestCase):
    def test_writes_inventory_to_excel(self):
        products = [
            {
                "product_url": "https://shop.test/sample-book",
                "title": "A Sample Book",
                "price_gbp": 12.5,
                "availability": "In stock",
            }
        ]

        fields = [
            "product_url",
            "title",
            "price_gbp",
            "availability",
        ]

        with TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "inventory.xlsx"

            write_xlsx(
                output_path,
                products,
                fields,
                sheet_name="Inventory",
            )

            self.assertTrue(output_path.exists())

            workbook = load_workbook(output_path, data_only=True)

            try:
                worksheet = workbook["Inventory"]

                self.assertEqual(worksheet["A1"].value, "product_url")
                self.assertEqual(worksheet["B2"].value, "A Sample Book")
                self.assertEqual(worksheet["C2"].value, 12.5)
                self.assertEqual(worksheet["D2"].value, "In stock")

                self.assertEqual(worksheet.freeze_panes, "A2")
                self.assertEqual(worksheet.auto_filter.ref, "A1:D2")

                self.assertEqual(
                    worksheet["C2"].number_format,
                    "£#,##0.00",
                )
            finally:
                workbook.close()


if __name__ == "__main__":
    unittest.main()