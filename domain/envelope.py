class Envelope:
    def __init__(self, id, name, balance) -> None:
        self.__id = id
        self.__name = name
        self.__balance = balance

    def pay(self, amount):
        self.__balance += amount

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    @property
    def balance(self):
        return self.__balance

    def update(self, value):
        self.__balance += value

    def rename(self, new_name):
        self.__name = new_name

    # convert from Envelope to json
    def to_doc(self):
        return {
            "id" : self.__id,
            "name": self.__name,
            "balance": round(self.__balance, 2)
        }

    # convert from json to Envelope
    @staticmethod
    def from_doc(data):
        return Envelope(data["id"], data["name"], data["balance"])