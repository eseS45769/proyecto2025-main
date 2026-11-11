import unittest
from decimal import Decimal
from types import SimpleNamespace
from backend.postgres import parameters, row_factory

class PostgresAdapter(unittest.TestCase):
    def test_literals_are_not_parameters(self):
        self.assertEqual(parameters("SELECT '?' AS text, id FROM usuarios WHERE id=? AND nombre LIKE 'A%'"), "SELECT '?' AS text, id FROM usuarios WHERE id=%s AND nombre LIKE 'A%%'")
    def test_row_preserves_mapping_and_positional_access(self):
        make = row_factory(SimpleNamespace(description=[SimpleNamespace(name='total')]))
        row = make([Decimal('12300')])
        self.assertEqual(row[0], 12300)
        self.assertEqual(dict(row), {'total':12300})
        self.assertIsInstance(row['total'], int)
