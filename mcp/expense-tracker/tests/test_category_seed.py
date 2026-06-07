from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from expense_tracker import repositories as repo
from expense_tracker.db import get_category_seed_path, init_db


class CategorySeedTests(unittest.TestCase):
    def test_seed_path_en(self) -> None:
        path = get_category_seed_path("en")
        self.assertTrue(path.name.endswith("seed-categories-en.sql"))

    def test_seed_path_es(self) -> None:
        path = get_category_seed_path("es")
        self.assertTrue(path.name.endswith("seed-categories-es.sql"))

    def test_seed_en_display_names(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        db_path = Path(tmp.name) / "test.db"
        os.environ["EXPENSE_DB_PATH"] = str(db_path)
        init_db(seed="categories", locale="en")
        names = {c["slug"]: c["name"] for c in repo.list_categories()}
        self.assertEqual(names["supermercado"], "Groceries")
        self.assertEqual(names["transporte"], "Transport")
        tmp.cleanup()

    def test_seed_es_display_names(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        db_path = Path(tmp.name) / "test.db"
        os.environ["EXPENSE_DB_PATH"] = str(db_path)
        init_db(seed="categories", locale="es")
        names = {c["slug"]: c["name"] for c in repo.list_categories()}
        self.assertEqual(names["supermercado"], "Supermercado")
        self.assertEqual(names["transporte"], "Transporte")
        tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
