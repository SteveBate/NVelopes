import unittest

from domain.account import Account
from domain.envelope import Envelope
from domain.payment_source import PaymentSource
from domain.payment_source_envelope import PaymentSourceEnvelope

class AccountTestFixture(unittest.TestCase):

    def test_account_is_correctly_initialised_when_created(self):
        # given
        acc = Account("12345", "MyBankName")
        # when
        acc.open("ABC1", "12345", 100.00)
        # then
        self.assertEqual(1, acc.envelope_count)
        self.assertEqual(100.00, acc.amount_in_envelope(0))
        self.assertEqual(100.00, acc.balance)
        self.assertEqual("Account Opened", acc.last_tx.description)
        self.assertIn("DEPOSIT              Account Opened                                     Available                                 100.00   100.00", acc.last_tx.to_string())


    def test_account_cannot_add_envelopes_with_default_amounts_that_total_more_than_account_balance(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.add_envelopes([Envelope(1, "Shopping", 101.00)])
        # then
        self.assertEqual("Not enough money to assign to the passed in envelopes. Required:  101.00, Actual:  100.00", str(ctx.exception))


    def test_account_cannot_add_envelope_with_id_of_0(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.add_envelopes([Envelope(0, "illegal", 0)])
        # then
            self.assertEqual("Envelope id 0 is reserved", str(ctx.exception))


    def test_account_can_add_envelopes(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        # when
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # then
        self.assertEqual(2, acc.envelope_count)


    def test_account_can_add_single_envelope(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        acc.add_envelope(Envelope(2, "Fuel", 0))
        # then
        self.assertEqual(3, acc.envelope_count)


    def test_account_can_list_envelopes(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        envelopes = acc.list_envelopes()
        # then
        self.assertEqual(2, envelopes.__len__())
        self.assertEqual("Available", envelopes[0].name)
        self.assertEqual("Shopping", envelopes[1].name)


    def test_account_can_rename_envelope(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        acc.rename_envelope(1, "Groceries")
        # then
        self.assertTrue(acc.envelope_exists("Groceries"))


    def test_account_can_rename_the_special_envelope(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        acc.rename_envelope(0, "Spare")
        # then
        self.assertTrue(acc.envelope_exists("Spare"))        


    def test_account_cannot_rename_envelope_to_an_empty_string(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.rename_envelope(1, "")
        # then
        self.assertEqual("new_name cannot be blank", str(ctx.exception))


    def test_account_cannot_rename_envelope_that_does_not_exist(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.rename_envelope(99, "Groceries")
        # then
        self.assertEqual("No envelope exists with id: 99", str(ctx.exception))  


    def test_account_can_deposit_amount_into_envelope(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        acc.deposit(1, "for shopping", 50.00)
        # then
        self.assertEqual(100.00, acc.amount_in_envelope(0))
        self.assertEqual(50.00, acc.amount_in_envelope(1))
        self.assertEqual(150.00, acc.balance)
        self.assertIn("DEPOSIT              for shopping                                       Shopping                                   50.00   150.00", acc.last_tx.to_string())


    def test_account_can_move_money_from_one_envelope_to_another(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        acc.move(0, 1, "for shopping", 70.00)
        # then
        self.assertEqual(30.00, acc.amount_in_envelope(0))
        self.assertEqual(70.00, acc.amount_in_envelope(1))
        self.assertEqual(100.00, acc.balance)
        self.assertIn("MOVE                 for shopping                                       Available -> Shopping                      70.00   100.00", acc.last_tx.to_string())


    def test_account_cannot_move_more_money_between_envelopes_than_is_available_in_source_envelope(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.move(0, 1, "for shopping", 101.00)
        # then
        self.assertEqual(f"Not enough money in '{acc.overflow_envelope_name}' envelope", str(ctx.exception))
        

    def test_account_can_debit_amount_from_envelope_with_funds(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        acc.debit(0, "paid bills", 100.00)
        # then
        self.assertEqual(0.00, acc.amount_in_envelope(0))
        self.assertEqual(0.00, acc.balance)
        self.assertIn("DEBIT                paid bills                                         Available                                -100.00     0.00", acc.last_tx.to_string())


    def test_account_can_debit_amount_from_envelope_with_more_funds_than_available_when_account_allowed_to_go_negative(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        acc.debit(0, "paid bills", 100.01)
        # then
        self.assertEqual(-0.01, round(acc.amount_in_envelope(0),2))
        self.assertEqual(-0.01, round(acc.balance, 2))
        self.assertIn("DEBIT                paid bills                                         Available                                -100.01    -0.01", acc.last_tx.to_string())


    def test_account_cannot_debit_amount_from_envelope_with_not_enough_funds_when_account_not_allowed_to_go_negative(self):
        # given
        acc = Account("12345", "MyBankName", False)
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.debit(0, "paid bills", 100.01)
        # then
        self.assertEqual("Cannot debit more than is available in 'Available' when account is not allowed to go negative", str(ctx.exception))


    def test_account_can_withdraw_amount_from_envelope_with_more_funds_than_available_when_account_allowed_to_go_negative(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        # when
        acc.atm(0, "paid bills", 100.01)
        # then
        self.assertEqual(-0.01, round(acc.amount_in_envelope(0),2))
        self.assertEqual(-0.01, round(acc.balance, 2))
        self.assertIn("ATM                  paid bills                                         Available                                -100.01    -0.01", acc.last_tx.to_string())


    def test_account_cannot_withdraw_amount_from_envelope_with_not_enough_funds_when_account_not_allowed_to_go_negative(self):
        # given
        acc = Account("12345", "MyBankName", False)
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.atm(0, "paid bills", 100.01)
        # then
        self.assertEqual("Cannot withdraw more than is available in 'Available' when account is not allowed to go negative", str(ctx.exception))


    # def test_account_can_correct_debit_transaction(self):
    #     # given
    #     acc = Account("12345", "MyBankName")
    #     acc.open("ABC1", "12345", 100.00)
    #     acc.debit(0, "paying out", 10.00)
    #     # when
    #     acc.correct(1, "paying out", 11.00)
    #     # then
    #     self.assertEqual(89.00, round(acc.amount_in_envelope(0),2))
    #     self.assertEqual(89.00, round(acc.balance, 2))
    #     self.assertIn("DEBIT                paying out                                         Available                                 -11.00", acc.last_tx.to_string())


    # def test_account_can_correct_deposit_transaction(self):
    #     # given
    #     acc = Account("12345", "MyBankName")
    #     acc.open("ABC1", "12345", 100.00)
    #     acc.deposit(0, "paying in", 10.00)
    #     # when
    #     acc.correct(1, "paying in", 11.00)
    #     # then
    #     self.assertEqual(111.00, round(acc.amount_in_envelope(0),2))
    #     self.assertEqual(111.00, round(acc.balance, 2))
    #     self.assertIn("DEPOSIT              paying in                                          Available                                  11.00", acc.last_tx.to_string())


    def test_account_can_debit_amount_from_envelope_then_undo(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        acc.debit(0, "paid bills", 100.00)
        # when
        acc.undo(acc.last_tx)        
        # then
        self.assertEqual(100.00, acc.amount_in_envelope(0))
        self.assertEqual(100.00, acc.balance)


    def test_account_can_deposit_amount_into_envelope_then_undo(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 0)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        acc.deposit(0, "some cash", 100.00)
        # when
        acc.undo(acc.last_tx)
        # then
        self.assertEqual(0, acc.amount_in_envelope(0))
        self.assertEqual(0, acc.balance)   

    def test_account_can_move_amount_between_envelopes_then_undo(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 100.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0)])
        acc.move(0, 1, "for shopping", 70.00)
        # when
        acc.undo(acc.last_tx)
        # then
        self.assertEqual(100.00, acc.amount_in_envelope(0))
        self.assertEqual(0, acc.amount_in_envelope(1))

    # def test_account_can_pay_envelopes_then_undo(self):
    #     # given
    #     acc = Account("12345", "MyBankName")
    #     acc.open("ABC1", "12345", 0.00)
    #     acc.add_envelopes([Envelope(1, "Shopping", 0), Envelope(2, "Savings", 0)])
    #     payment_source = PaymentSource(0, "ACME Ltd.", 300.00, [PaymentSourceEnvelope(1, 100.00), PaymentSourceEnvelope(2, 100.00)])
    #     acc.pay("Pay day!", payment_source)
    #     # when
    #     acc.undo(acc.last_tx)
    #     # then
    #     self.assertEqual(0.00, acc.amount_in_envelope(0))
    #     self.assertEqual(0.00, acc.amount_in_envelope(1))
    #     self.assertEqual(0.00, acc.amount_in_envelope(2))         


    # def test_account_can_debit_amount_from_envelope_then_undo_then_redo(self):
    #     # given
    #     acc = Account("12345", "MyBankName")
    #     acc.open("ABC1", "12345", 100.00)
    #     acc.add_envelopes([Envelope(1, "Shopping", 0)])
    #     acc.debit(0, "paid bills", 100.00)
    #     acc.undo()
    #     # when
    #     acc.redo()
    #     # then
    #     self.assertEqual(0.00, acc.amount_in_envelope(0))
    #     self.assertEqual(0.00, acc.balance)
    #     self.assertIn("DEBIT                paid bills                                         Available                                -100.00", acc.last_tx.to_string())

    def test_account_can_specify_payment_source_and_amounts_to_pay_into_each_envelope(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 0.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0), Envelope(2, "Savings", 0), Envelope(3, "Gas/Electric", 0)])
        # when
        acc.add_payment_source(PaymentSource(0, "Umbrella Corporation", 1000.00, [PaymentSourceEnvelope(1, 600), PaymentSourceEnvelope(2, 200), PaymentSourceEnvelope(3, 150)]))
        # then
        self.assertEqual(acc.pay_source_count, 1)

    def test_account_can_specify_second_payment_source_and_amounts_to_pay_into_each_envelope(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 0.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0), Envelope(2, "Savings", 0), Envelope(3, "Gas/Electric", 0), Envelope(4, "Loan", 0)])
        # when
        acc.add_payment_source(PaymentSource(0, "Umbrella Corporation", 1000.00, [PaymentSourceEnvelope(1, 600), PaymentSourceEnvelope(2, 200), PaymentSourceEnvelope(3, 150)]))
        acc.add_payment_source(PaymentSource(0, "Massive Dynamic", 500.00, [PaymentSourceEnvelope(4, 250)]))
        # then
        self.assertEqual(acc.pay_source_count, 2)

    def test_account_does_not_allow_payment_source_to_specify_envelopes_that_it_does_not_contain(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 0.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0), Envelope(2, "Savings", 0), Envelope(3, "Gas/Electric", 0)])
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.add_payment_source(PaymentSource(0, "Umbrella Corporation", 1000.00, [PaymentSourceEnvelope(99, 600)]))
        # then
        self.assertEqual("pay_source must only contain ids of existing account envelopes", str(ctx.exception))

    def test_account_can_pay_and_distribute_money_into_designated_envelopes__and_assigns_remainder_to_available_envelope(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 0.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0), Envelope(2, "Savings", 0)])
        payment_source = PaymentSource(0, "ACME Ltd.", 1100.00, [PaymentSourceEnvelope(1, 700.00), PaymentSourceEnvelope(2, 300.00)])
        # when
        acc.pay("Pay day!", payment_source)
        # then
        self.assertEqual(100.00, acc.amount_in_envelope(0))
        self.assertEqual(700.00, acc.amount_in_envelope(1))
        self.assertEqual(300.00, acc.amount_in_envelope(2))
        self.assertIn("PAY                  ACME Ltd. - Pay day!                                                                        1100.00  1100.00", acc.last_tx.to_string())

    def test_account_does_not_accept_pay_that_totals_less_than_declared_envelope_values(self):
        # given
        acc = Account("12345", "MyBankName")
        acc.open("ABC1", "12345", 0.00)
        acc.add_envelopes([Envelope(1, "Shopping", 0), Envelope(2, "Savings", 0)])
        payment_source = PaymentSource(0, "ACME Ltd.", 900.00, [PaymentSourceEnvelope(1, 700.00), PaymentSourceEnvelope(2, 300.00)])
        # when
        with self.assertRaises(ValueError) as ctx:
            acc.pay("Pay day!", payment_source)
        # then
        self.assertIn("Payment amount must equal or exceed the sum total of payment source envelopes", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
