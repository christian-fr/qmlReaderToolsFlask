from pymongo import MongoClient


def add_to_db(mc: MongoClient, db_name: str, coll_name: str, data: dict):
    db = mc.get_database(db_name)
    coll = db.get_collection(coll_name)
    ids = coll.insert_one(data)
    db.get_collection(coll_name)
    cursor = coll.find({})
    for e in cursor:
        print(e)
    print()
