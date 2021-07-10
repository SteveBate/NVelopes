from domain.payment_source_envelope import PaymentSourceEnvelope
from typing import List

class PaymentSource:
    def __init__(self, id, payer, amount, payment_source_envelopes: List[PaymentSourceEnvelope]):
        self.__id = id
        self.__payer = payer
        self.__amount = amount
        self.__payment_source_envelopes = payment_source_envelopes

    @property
    def id(self):
        return self.__id

    @property
    def payer(self):
        return self.__payer

    @property
    def amount(self):
        return self.__amount

    @property
    def envelopes(self):
        return self.__payment_source_envelopes

    # convert from PaymentSource to json
    def to_doc(self):
        return {
            "id" : self.__id,
            "payer" : self.__payer,
            "amount": self.__amount,
            "envelopes": [pse.to_doc() for pse in self.__payment_source_envelopes]
        }

    # convert from json to PaymentSource
    @staticmethod
    def from_doc(data):
        envelopes = [PaymentSourceEnvelope(d["id"], d["amount"]) for d in data["envelopes"]]
        return PaymentSource(data["id"], data["payer"], data["amount"], envelopes)
