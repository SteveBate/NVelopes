from datetime import datetime
from typing import List
from domain.payment_source_envelope import PaymentSourceEnvelope

class Transaction:
    def __init__(self, tx_id, owner_id, account_id, envelope_id_src, envelope_id_dest, envelope, op, description, amount, account_balance, pay_envelopes: List[PaymentSourceEnvelope]=None) -> None:
        self.__date = datetime.now()
        self.__tx_id = tx_id
        self.__owner_id = owner_id
        self.__account_id = account_id
        self.__envelope_id_src = envelope_id_src
        self.__envelope_id_dest = envelope_id_dest
        self.__envelope = envelope
        self.__op = op
        self.__description = description
        self.__amount = amount
        self.__account_balance = account_balance
        self.__pay_envelopes = pay_envelopes

    # allow correction of this transactions's description and amount
    def correct(self, description, amount):
        self.__description = description if description == "" else self.__description
        self.__amount = amount if amount != 0 else self.__amount

    @property
    def id(self):
        return self.__tx_id

    @property
    def owner_id(self):
        return self.__owner_id

    @property
    def account_id(self):
        return self.__account_id

    @property
    def envelope_id_src(self):
        return self.__envelope_id_src

    @property
    def envelope_id_dest(self):
        return self.__envelope_id_dest

    @property
    def operation(self):
        return self.__op

    @property
    def description(self):
        return self.__description

    @property
    def amount(self):
        return self.__amount

    @property
    def account_balance(self):
        return self.__account_balance

    @property
    def pay_envelopes(self):
        return self.__pay_envelopes

    # textual representation of a transaction
    def to_string(self):
        return f"{self.__tx_id:<15} {self.__date.strftime('%M-%D-%Y %I:%M:%S'):<25} {self.__op:<20} {self.__description:<50} {self.__envelope:<40} {self.__amount:7.2f}  {self.__account_balance:7.2f}"

    # convert from Transaction to json
    def to_doc(self):
        return {
            "date": self.__date,
            "tx_id" : self.__tx_id,
            "owner_id" : str(self.__owner_id),
            "account_id" : str(self.__account_id),
            "envelope_id_src": self.__envelope_id_src,
            "envelope_id_dest": self.__envelope_id_dest,
            "envelope": self.__envelope,
            "op": self.__op,
            "description": self.__description,
            "amount": self.__amount,
            "account_balance": self.__account_balance,
            "pay_envelopes": self.__pay_envelopes
        }
    
    # convert from json to Transaction
    @staticmethod
    def from_doc(data):
        return Transaction(data["tx_id"], data["owner_id"], data["account_id"], data["envelope_id_src"], data["envelope_id_dest"], data["envelope"], data["op"], data["description"], data["amount"], data["account_balance"], data["pay_envelopes"])
