from account import Account
from envelope import Envelope
from payment_source import PaymentSource
from payment_source_envelope import PaymentSourceEnvelope

# create an account with an opening balance
acc = Account("My Current Account", 100)

# create the Envelopes for budgeting
acc.add_Envelopes([
    Envelope(0, "Available", 0),
    Envelope(1, "Shopping", 0),
    Envelope(2, "Mortgage", 0),
    Envelope(3, "Loans", 0),
    Envelope(4, "Council Tax", 0),
    Envelope(5, "Car", 0),
    Envelope(6, "Utilities", 0),
    Envelope(7, "Savings", 0),
    Envelope(8, "Wife's hairdressing", 0),
    Envelope(9, "My habit", 0),
    Envelope(10, "Entertainment", 0),
    Envelope(11, "Vets", 0),
    Envelope(12, "Car Maintenance", 0)
])

# create wages representing employers and which Envelopes they will "pay"
wage1 = PaymentSource("Massive Dynamic", 3000.00, [
    PaymentSourceEnvelope(1, 800.00),
    PaymentSourceEnvelope(2, 753.61),
    PaymentSourceEnvelope(3, 168.00),
    PaymentSourceEnvelope(4, 185.00),
    PaymentSourceEnvelope(5, 109.26),
    PaymentSourceEnvelope(6, 107.00),
])

wage2 = PaymentSource("Umbrella Corporation", 1000.00, [
    PaymentSourceEnvelope(7, 300.00),
    PaymentSourceEnvelope(8, 60.00),
    PaymentSourceEnvelope(9, 50.00),
    PaymentSourceEnvelope(10, 60.00),
    PaymentSourceEnvelope(11, 50.00),
    PaymentSourceEnvelope(12, 50.00)
])

# Envelopes can be added later too
acc.add_Envelope(Envelope(13, "Dentist", 0))

# Exercise the model with some life-like data 
acc.print_Envelopes()
acc.pay("Payday", wage1)
acc.deposit(7, "Birthday money", 150.00)
acc.debit(1, "Big Shop", 450.00)
acc.correct(2, "Birthday money", 160.00)
acc.pay("Payday", wage2)
acc.debit(2, "Monthly Mortgage Payment", 753.61)
acc.debit(9, "xxxx", 75.00)
acc.move(7, 9, "hush money", 25.00)
acc.undo()
acc.redo()
acc.print_history()
acc.print_Envelopes()