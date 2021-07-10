class PaymentSourceEnvelope:
    def __init__(self, id, amount) -> None:
        self.__id = id
        self.__amount = amount

    @property
    def id(self):
        return self.__id

    @property
    def amount(self):
        return self.__amount

    # convert from PaymentSourceEnvelope to json
    def to_doc(self):
        return {
            "id" : self.__id,
            "amount": self.__amount
        }

    # convert from json to PaymentSourceEnvelope
    @staticmethod
    def from_doc(data):
        return PaymentSourceEnvelope(data["id"], data["amount"])