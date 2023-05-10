from unittest import TestCase
from mongomock import MongoClient
from qform.dbutil import add_to_db


class Test(TestCase):
    def setUp(self) -> None:
        self.mongo_client = MongoClient()

    def test_fn_to_test(self):
        add_to_db(self.mongo_client, "exampleDb", "exampleCollection", {'this': 'that'})
        self.fail()
