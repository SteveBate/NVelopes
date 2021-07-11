from domain.payment_source_envelope import PaymentSourceEnvelope
from .payment_source import PaymentSource
from .envelope import Envelope
from .transaction import Transaction
from typing import List

class Account:

    # constants
    __OVERFLOW_ENVELOPE_ID = 0

    # private
    __balance = 0
    __can_go_negative = True
    __last_tx = None
    __last_tx_id = -1
    __pay_sources: List[PaymentSource] = []

    # constructor
    def __init__(self, owner_id, name, allow_negative = True) -> None:
        self.__owner_id = owner_id
        self.__name = name
        self.__envelopes = [Envelope(0, "Available", 0)]
        self.__pay_sources = []
        self.__can_go_negative = allow_negative


    # associate envelope with account
    def add_envelope(self, envelope: Envelope) -> None:
        envelope_total = sum(e.balance for e in self.__envelopes)
        if envelope.balance > self.balance - envelope_total: raise ValueError("Not enough money to assign to the passed in envelope")
        self.__envelopes.append(envelope)


    # associate multiple envelopes with account in one go
    def add_envelopes(self, envelopes: list) -> None:
        envelope_total_req = sum(e.balance for e in envelopes)
        money_in_account = self.balance
        if money_in_account < envelope_total_req: raise ValueError(str(f"Not enough money to assign to the passed in envelopes. Required: {envelope_total_req:7.2f}, Actual: {self.balance:7.2f}"))
        for e in envelopes:
            if (e.id == 0): raise ValueError("envelope id 0 is reserved")
            self.__envelopes.append(e)


    # associate envelope with account
    def rename_envelope(self, envelope_id: int, new_name: str) -> None:
        if new_name == "":
            raise ValueError("new_name cannot be blank")
        if not bool([e for e in self.__envelopes if (e.id == envelope_id)]):
            raise ValueError(f"No envelope exists with id: {envelope_id}")
        self.__envelopes[envelope_id].rename(new_name)


    # add a source of regular income i.e. an employer, in which to pay into envelopes
    def add_payment_source(self, pay_source: PaymentSource) -> None:
        # check that envelopes exist with ids matching those designated as targets for a payment source        
        valid = all(id in [x.id for x in self.__envelopes] for id in [x.id for x in pay_source.envelopes])
        if not valid:
            raise ValueError("pay_source must only contain ids of existing account envelopes")
        self.__pay_sources.append(pay_source)


    # add a source of regular income i.e. an employer, in which to pay into envelopes
    def update_payment_source(self, pay_source_id: int, pay_source: PaymentSource) -> None:
        # check that envelopes exist with ids matching those designated as targets for a payment source        
        valid = all(id in [x.id for x in self.__envelopes] for id in [x.id for x in pay_source.envelopes])
        if not valid:
            raise ValueError("pay_source must only contain ids of existing account envelopes")
        self.__pay_sources[pay_source_id] = pay_source


    # record a payment in each envelope
    def pay(self, description, pay_source: PaymentSource) -> None:
        required_total = sum(p.amount for p in pay_source.envelopes)
        if pay_source.amount < required_total : raise ValueError(str(f"Payment amount must equal or exceed the sum total of payment source envelopes"))
        for e in pay_source.envelopes: self.__envelopes[e.id].pay(e.amount)
        total = sum(p.amount for p in pay_source.envelopes)
        self.__envelopes[self.__OVERFLOW_ENVELOPE_ID].update(pay_source.amount - total)
        self.__balance += pay_source.amount
        self.__last_tx = Transaction(self.__inc_tx_id(), self.__owner_id, self.__account_id, -1, -1, "", "PAY", f"{pay_source.payer} - {description}", pay_source.amount, self.__balance, pay_envelopes=[e.to_doc() for e in pay_source.envelopes])
        return self.__envelopes

    def open(self, account_id, owner_id, amount) -> None:        
        self.__account_id = account_id
        self.__owner_id = owner_id
        self.__envelopes[0].update(amount)
        self.__balance = amount
        self.__last_tx = Transaction(self.__inc_tx_id(), self.__owner_id, self.__account_id, self.__OVERFLOW_ENVELOPE_ID, -1, self.overflow_envelope_name, "DEPOSIT", "Account Opened", amount, amount)


    def deposit(self, envelope_id, description, amount) -> Envelope:
        self.__envelopes[envelope_id].update(amount)
        self.__balance += amount
        self.__last_tx = Transaction(self.__inc_tx_id(), self.__owner_id, self.__account_id, envelope_id, -1, self.__envelopes[envelope_id].name, "DEPOSIT", description, amount, self.__balance)
        return self.__envelopes[envelope_id]


    def debit(self, envelope_id, description, amount) -> Envelope:
        if self.__envelopes[envelope_id].balance - amount < 0 and not self.__can_go_negative: raise(ValueError(str(f"Cannot debit more than is available in '{self.__envelopes[envelope_id].name}' when account is not allowed to go negative")))
        self.__envelopes[envelope_id].update(-amount)
        self.__balance -= amount
        self.__last_tx = Transaction(self.__inc_tx_id(), self.__owner_id, self.__account_id, envelope_id, -1, self.__envelopes[envelope_id].name, "DEBIT", description, -amount, self.__balance)
        return self.__envelopes[envelope_id]


    def atm(self, envelope_id, description, amount) -> None:
        if self.__envelopes[envelope_id].balance - amount < 0 and not self.__can_go_negative: raise(ValueError(str(f"Cannot withdraw more than is available in '{self.__envelopes[envelope_id].name}' when account is not allowed to go negative")))
        self.__envelopes[envelope_id].update(-amount)
        self.__balance -= amount
        self.__last_tx = Transaction(self.__inc_tx_id(), self.__owner_id, self.__account_id, envelope_id, -1, self.__envelopes[envelope_id].name, "ATM", description, -amount, self.__balance)


    # move money between envelopes
    def move(self, src_id, dest_id, description, amount) -> List[Envelope]:
        if self.__envelopes[src_id].balance < amount: raise ValueError(str(f"Not enough money in '{self.__envelopes[src_id].name}' envelope"))
        self.__envelopes[src_id].update(-amount)
        self.__envelopes[dest_id].update(amount)
        self.__last_tx = Transaction(self.__inc_tx_id(), self.__owner_id, self.__account_id, src_id, dest_id, f"{self.__envelopes[src_id].name} -> {self.__envelopes[dest_id].name}", "MOVE", description, amount, self.__balance)
        return [self.__envelopes[src_id], self.__envelopes[dest_id]] # changed envelopes


    # undo the last transaction
    def undo(self, tx: Transaction) -> List[Envelope]:
        if tx.operation == "MOVE":
            self.__envelopes[tx.envelope_id_src].update(tx.amount)
            self.__envelopes[tx.envelope_id_dest].update(-tx.amount)
            self.__last_tx = None
            self.__last_tx_id = self.__last_tx_id - 1
            return self.__envelopes        
        if tx.operation == "DEBIT" or tx.operation == "ATM":
            self.__balance = self.__balance + abs(tx.amount)
            self.__envelopes[tx.envelope_id_src].update(abs(tx.amount))
            self.__last_tx = None
            self.__last_tx_id = self.__last_tx_id - 1
            return self.__envelopes            
        if tx.operation == "DEPOSIT":
            self.__balance = self.__balance - abs(tx.amount)
            self.__envelopes[tx.envelope_id_src].update(-tx.amount)
            self.__last_tx = None
            self.__last_tx_id = self.__last_tx_id - 1
            return self.__envelopes
        if tx.operation == "PAY":
            # undo the account balance
            self.__balance = self.__balance - tx.amount
            # undo each envelope
            pse = [PaymentSourceEnvelope.from_doc(pe) for pe in tx.pay_envelopes]
            for pe in pse:
                self.__envelopes[pe.id].update(-pe.amount)
            # whatever remainder was pushed into the overflow envelope needs to be undone too
            total = sum(p.amount for p in pse)
            diff = tx.amount -total
            self.__envelopes[self.__OVERFLOW_ENVELOPE_ID].update(-diff)
            # set the transaction state for the account
            self.__last_tx = None
            self.__last_tx_id = self.__last_tx_id - 1
            # return changes
            return self.__envelopes


    def envelope_exists(self, envelope_name):
        return bool([e for e in self.__envelopes if (e.name == envelope_name)])


    # return how much money is in a envelope
    def amount_in_envelope(self, envelope_id) -> float:
        return self.__envelopes[envelope_id].balance


    def list_envelopes(self):
        return self.__envelopes


    def list_pay_sources(self):
        return self.__pay_sources


    # print current state of envelopes
    def print_envelopes(self) -> None:
        print("envelope list:")
        for e in self.__envelopes:
            print(f"{e.name:<40} {e.balance:7.2f}")
        print("")
        print("")


    # generate the next transaction id
    def __inc_tx_id(self) -> int:
        self.__last_tx_id += 1
        return self.__last_tx_id


    @property
    def id(self):
        return self.__account_id


    @property
    def name(self):
        return self.__name


    @property
    def pay_source_count(self):
        return self.__pay_sources.__len__()        


    @property
    def can_go_negative(self):
        return self.__can_go_negative


    @can_go_negative.setter
    def can_go_negative(self, value):
        self.can_go_negative = value


    # return number of envelopes for this account
    @property
    def envelope_count(self) -> int:
        return self.__envelopes.__len__()


    # get last envelope
    @property
    def last_envelope(self) -> Envelope:
        return self.__envelopes[-1]


    # get the name of the special overflow envelope
    @property
    def overflow_envelope_name(self) -> str:
        return self.__envelopes[0].name


    # get last transaction
    @property
    def last_tx(self) -> Transaction:
        return self.__last_tx


    # get last transaction id
    @property
    def last_tx_id(self) -> int:
        return self.__last_tx_id


    # current balance of the account
    @property
    def balance(self) -> float:
        return self.__balance


    # convert from Account to json
    def to_doc(self):
        return {
            "owner_id" : self.__owner_id,
            "name": self.__name,
            "balance": self.__balance,
            "last_tx_id": self.__last_tx_id,
            "can_go_negative": self.__can_go_negative,
            "envelopes": [e.to_doc() for e in self.__envelopes],
            "payment_sources": [p.to_doc() for p in self.__pay_sources]
        }


    # convert from json to Account
    @staticmethod
    def from_doc(data):
        acc = Account(data["owner_id"], data["name"], data["can_go_negative"])
        acc.__account_id = data["_id"]
        acc.__owner_id = data["owner_id"]
        acc.__name =  data["name"]
        acc.__balance = data["balance"]
        acc.__last_tx_id = data["last_tx_id"]
        acc.__can_go_negative = data["can_go_negative"]        
        acc.__envelopes = [Envelope(d["id"], d["name"], d["balance"]) for d in data["envelopes"]]
        acc.__pay_sources = [PaymentSource(d["id"], d["payer"], d["amount"], d["envelopes"]) for d in data["payment_sources"]]
        return acc