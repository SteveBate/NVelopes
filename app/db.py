import os
import pymongo
from bson.objectid import ObjectId
from pymongo import cursor
from domain.account import Account
from domain.envelope import Envelope
from domain.payment_source import PaymentSource
from typing import List

# the connection string is different depending on how the application is executed.
# if the database is external e.g. hosted on Mongo Cloud Atlas then that connection string is the one we define and use in our docker environment variable
# if the database is running locally but in containers like in this application then the following applies:

# 1. when our app is running inside a container via DOCKER RUN (-e flag) or DOCKER COMPOSE (environment section)
# the connction string needs to use all the dns names as defined in the docker compose file to see the database on the same docker network:
# mongodb://dbUser:dbPw0rd@mongo1:27017,mongo2:27017,mongo3:27017/nvelopes?authSource=nvelopes&replicaSet=rs0&readPreference=primary&ssl=false

# 2. when our app is running outside of a container i.e. locally, the dns names are not known therefore we use the localhost version via a .env file:
# mongodb://dbUser:dbPw0rd@localhost:27011/?authSource=nvelopes&readPreference=primary&ssl=false

myclient = pymongo.MongoClient(os.environ['DB_CONNECTION_STRING'])

class Db:
    def __init__(self) -> None:
        print("creating database")
        print("connection: " + os.environ['DB_CONNECTION_STRING'])
        self.__db = myclient["nvelopes"]


    def get_user(self, name: str):
        users = self.__db.get_collection("users")
        return users.find_one({ "username": name })


    def insert_user(self, user) -> str:
        users = self.__db.get_collection("users")
        result = users.insert_one(user.__dict__)
        # return result.inserted_id
        id: str = (result.inserted_id)
        return id


    def get_account(self, owner_id, account_id):
        from bson.objectid import ObjectId
        accounts = self.__db.get_collection("accounts")
        return accounts.find_one({ '_id': ObjectId(account_id), 'owner_id': owner_id})


    def get_transactions(self, owner_id, account_id, page, take):
        transactions = self.__db.get_collection("transactions")
        return transactions.find({'account_id': account_id, 'owner_id': owner_id}).skip(page*take).limit(take)


    def get_transaction(self, owner_id, account_id, tx_id):
        transactions = self.__db.get_collection("transactions")
        return transactions.find_one({'account_id': account_id, 'owner_id': owner_id, 'tx_id': tx_id})


    def get_last_transaction(self, owner_id, account_id):
        transactions = self.__db.get_collection("transactions")
        cursor = transactions.find({ 'account_id': account_id, 'owner_id': owner_id}).sort('tx_id', direction=pymongo.DESCENDING).limit(1)
        tx = list(cursor)[0]
        return tx


    def create_account(self, account: Account):                
        accounts = self.__db.get_collection("accounts")
        result = accounts.insert_one(account.to_doc())
        return result.inserted_id


    def open_account(self, account: Account):
        with myclient.start_session() as session:
            with session.start_transaction():        
                accounts = self.__db.get_collection("accounts")
                txs = self.__db.get_collection("transactions")
                result = accounts.replace_one({'_id': ObjectId(account.id)}, account.to_doc(), session=session)
                txs.insert_one(account.last_tx.to_doc(), session=session)
                return result.modified_count > 0


    def add_payment_source(self, account_id, payment_source: PaymentSource):
        print(payment_source.to_doc())
        from bson.objectid import ObjectId
        accounts = self.__db.get_collection("accounts")
        result = accounts.update_one({ '_id': ObjectId(account_id)}, { '$push': {'payment_sources': payment_source.to_doc() }})
        return result.modified_count > 0


    def replace_payment_source(self, account_id, payment_source_id, payment_source: PaymentSource):
        from bson.objectid import ObjectId
        accounts = self.__db.get_collection("accounts")
        result = accounts.update_one({ '_id': ObjectId(account_id)}, { '$set': { f'payment_sources.{payment_source_id}': payment_source.to_doc() }})
        return result.modified_count > 0        


    def add_envelope(self, account_id, envelope):
        from bson.objectid import ObjectId
        accounts = self.__db.get_collection("accounts")
        result = accounts.update_one({ '_id': ObjectId(account_id)}, { '$push': {'envelopes': envelope.to_doc() }})
        return result.modified_count > 0


    def add_envelopes(self, account_id, envelopes):
        from bson.objectid import ObjectId
        docs = list(map(lambda b: b.to_doc(), envelopes))
        accounts = self.__db.get_collection("accounts")
        result = accounts.update_one({ '_id': ObjectId(account_id)}, { '$push': {'envelopes': { '$each':  docs } }})
        return result.modified_count > 0


    def rename_envelope(self, account_id, envelope_id, new_name):
        from bson.objectid import ObjectId
        accounts = self.__db.get_collection("accounts")
        result = accounts.update_one({ '_id': ObjectId(account_id)}, { '$set': { f"envelopes.{envelope_id}.name": new_name } })
        return result.modified_count > 0        


    def save_envelope_change(self, account: Account, envelope: Envelope):
        from bson.objectid import ObjectId
        # wrap two updates in an auto-commited transaction (auto-rollback on error)
        with myclient.start_session() as session:
            with session.start_transaction():
                accounts = self.__db.get_collection("accounts")
                transactions = self.__db.get_collection("transactions")
                result1 = accounts.update_one({ '_id': ObjectId(account.id)}, { '$set': { "last_tx_id": account.last_tx_id, "balance": account.balance, f"envelopes.{envelope.id}": envelope.to_doc()} }, session=session)
                result2 = transactions.insert_one(account.last_tx.to_doc(), session=session)
                return result1.modified_count == 1 and result2.acknowledged


    def save_envelope_changes(self, account: Account, from_envelope: Envelope, to_envelope: Envelope):
        from bson.objectid import ObjectId
        # wrap two updates in an auto-commited transaction (auto-rollback on error)
        with myclient.start_session() as session:
            with session.start_transaction():
                accounts = self.__db.get_collection("accounts")
                transactions = self.__db.get_collection("transactions")
                result1 = accounts.update_one({ '_id': ObjectId(account.id)}, { '$set': { "last_tx_id": account.last_tx_id, "balance": account.balance, f"envelopes.{from_envelope.id}": from_envelope.to_doc(),  f"envelopes.{to_envelope.id}": to_envelope.to_doc() }}, session=session)
                result2 = transactions.insert_one(account.last_tx.to_doc(), session=session)
                return result1.modified_count == 1 and result2.acknowledged


    def save_all_envelopes(self, account: Account, envelopes: List[Envelope]):
        from bson.objectid import ObjectId
        # wrap two updates in an auto-commited transaction (auto-rollback on error)
        with myclient.start_session() as session:
            with session.start_transaction():
                docs = list(map(lambda b: b.to_doc(), envelopes))
                accounts = self.__db.get_collection("accounts")
                transactions = self.__db.get_collection("transactions")
                result1 = accounts.update_one({ '_id': ObjectId(account.id)}, { '$set': { "last_tx_id": account.last_tx_id, "balance": account.balance, "envelopes": docs }}, session=session)
                result2 = transactions.insert_one(account.last_tx.to_doc(), session=session)
                return result1.modified_count == 1 and result2.acknowledged


    def save_all_changes_after_undo(self, account: Account, envelopes: List[Envelope]):
        from bson.objectid import ObjectId
        # wrap two updates in an auto-commited transaction (auto-rollback on error)
        with myclient.start_session() as session:
            with session.start_transaction():
                docs = list(map(lambda b: b.to_doc(), envelopes))
                accounts = self.__db.get_collection("accounts")
                transactions = self.__db.get_collection("transactions")
                result1 = accounts.update_one({ '_id': ObjectId(account.id)}, { '$set': { "last_tx_id": account.last_tx_id, "balance": account.balance, "envelopes": docs }}, session=session)
                result2 = transactions.delete_one({'account_id': str(account.id), 'tx_id': account.last_tx_id+1}, session=session)
                print(result2.deleted_count)
                return result1.modified_count == 1 and result2.deleted_count == 1


# export the database instance
db = Db()