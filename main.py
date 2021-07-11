from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

import os
import app.auth as auth
from datetime import timedelta
from fastapi import Depends, HTTPException, FastAPI, status
from fastapi.security import OAuth2PasswordRequestForm
from app.requests import NewUserRequest, NewAccountRequest, AddEnvelopesRequest, AddEnvelopeRequest, MoveMoneyRequest, DepositMoneyRequest, DebitMoneyRequest
from app.requests import AddPaymentSourceRequest, UpdatePaymentSourceRequest, PayRequest, RenameEnvelopesRequest, UndoRequest
from app.models import Token, User, UserInDB
from app.db import db
from domain.account import Account
from domain.envelope import Envelope
from domain.payment_source import PaymentSource
from domain.payment_source_envelope import PaymentSourceEnvelope
from domain.transaction import Transaction

app = FastAPI()


# domain endpoints - most requests follow a similar pattern e.g. load the account, invoke the domain method to sense check what is allowed, then update the database

@app.post("/accounts/new")
def create_new_account(req: NewAccountRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    acc = Account(token.user_id, req.name, req.can_go_negative)
    result = db.create_account(acc)
    account_id = result.__str__()
    acc.open(account_id, token.user_id, req.opening_balance)
    db.open_account(acc)
    return { "AccountId": account_id, "Account": acc.name, "Status": "Opened", "Balance": acc.balance }
      

@app.post("/accounts/envelopes/add")
def add_envelopes_to_account(req: AddEnvelopesRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    envelope_list = [Envelope(i+1, b, 0) for i, b in enumerate(req.envelopes)]
    acc.add_envelopes(envelope_list)
    success = db.add_envelopes(req.account_id, envelope_list)
    return success


@app.post("/accounts/envelopes/addsingle")
def add_single_envelope_to_account(req: AddEnvelopeRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    env = Envelope(acc.last_envelope.id+1, req.envelope, 0)
    acc.add_envelope(env)
    success = db.add_envelope(req.account_id, env)
    return success


@app.post("/accounts/envelopes/rename")
def rename_envelope(req: RenameEnvelopesRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    acc.rename_envelope(req.envelope_id, req.new_name)
    success = db.rename_envelope(req.account_id, req.envelope_id, req.new_name)
    return success    


@app.post("/accounts/payers/add")
def add_payment_source_to_account(req: AddPaymentSourceRequest, token: UserInDB = Depends(auth.get_current_active_user)):    
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    id = acc.pay_source_count
    source = PaymentSource(id, req.payer, req.amount, [PaymentSourceEnvelope(x.envelope_id, x.amount) for x in req.payments])
    acc.add_payment_source(source)
    return db.add_payment_source(req.account_id, source)


@app.post("/accounts/payers/update")
def add_payment_source_to_account(req: UpdatePaymentSourceRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    source = PaymentSource(req.payment_source_id, req.payer, req.amount, [PaymentSourceEnvelope(x.envelope_id, x.amount) for x in req.payments])
    acc.update_payment_source(req.payment_source_id, source)
    return db.replace_payment_source(req.account_id, req.payment_source_id, source)    


@app.post("/accounts/movemoney")
def move_money(req: MoveMoneyRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    changes = acc.move(req.from_id, req.to_id, req.description, req.amount)
    success = db.save_envelope_changes(acc, changes[0], changes[1])
    return success


@app.post("/accounts/deposit")
def deposit(req: DepositMoneyRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    changed_envelope = acc.deposit(req.envelope_id, req.description, req.amount)
    success = db.save_envelope_change(acc, changed_envelope)
    return success


@app.post("/accounts/debit")
def debit(req: DebitMoneyRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    changed_envelope = acc.debit(req.envelope_id, req.description, req.amount)
    success = db.save_envelope_change(acc, changed_envelope)
    return success
    

@app.post("/accounts/pay")
def add_payment_source_to_account(req: PayRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    source = PaymentSource(req.payment_source_id, req.payer, req.amount, [PaymentSourceEnvelope(x.envelope_id, x.amount) for x in req.payments])
    doc = db.get_account(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    try:
        envelopes = acc.pay(req.description, source)
        return db.save_all_envelopes(acc, envelopes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/accounts/transactions/undo")
def undo(req: UndoRequest, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_last_transaction(token.user_id, req.account_id)
    if not doc: raise HTTPException(status_code=404, detail="Transaction not found")
    tx = Transaction.from_doc(doc)
    if tx.id == 0: raise HTTPException(status_code=400, detail="Cannot undo opening transaction. Delete the account instead.")
    acc = Account.from_doc(db.get_account(token.user_id, req.account_id))
    try:
        envelopes = acc.undo(tx)
        return db.save_all_envelopes_after_undo(acc, envelopes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accounts/{account_id}")
def get_account(account_id: str, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    return { "account_id" : account_id, "name": acc.name, "balance": acc.balance, "envelopes": [e.to_doc() for e in acc.list_envelopes()], "paysources": [{ "id": p.id, "payer": p.payer, "amount": p.amount, "envelopes": p.envelopes } for p in acc.list_pay_sources()] }


@app.get("/accounts/{account_id}/transactions/{page}/{size}")
def get_transactions(account_id: str, page: int, size: int, token: UserInDB = Depends(auth.get_current_active_user)):    
    docs = db.get_transactions(token.user_id, account_id, page, size)
    if not docs: raise HTTPException(status_code=404, detail="Transactions not found") 
    # return docs # error - not subscriptable
    # return [Transaction.from_doc(d) for d in docs] # returns field names as properties e.g. __Transaction__tx_id    
    return [t.to_doc() for t in [Transaction.from_doc(d) for d in docs]] # convert retrieved results to Transaction then back to doc gives desired result


@app.get("/accounts/{account_id}/envelopes/list")
def get_envelopes(account_id: str, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    return [e.to_doc() for e in acc.list_envelopes()]


@app.get("/accounts/{account_id}/paysources/list")
def get_paysources(account_id: str, token: UserInDB = Depends(auth.get_current_active_user)):
    doc = db.get_account(token.user_id, account_id)
    if not doc: raise HTTPException(status_code=404, detail="Account not found")
    acc = Account.from_doc(doc)
    return [{ "id": p.id, "payer": p.payer, "amount": p.amount, "envelopes": p.envelopes } for p in acc.list_pay_sources()]


# user endpoints

@app.get("/users/me")
def read_users_me(current_user: User = Depends(auth.get_current_active_user)):
    return { "username": current_user.username, "email": current_user.email, "full_name": current_user.full_name, "disabled": current_user.disabled }


@app.get("/users/exists/{username}")
def check_if_user_exists(username):
    print("/users/checkusername")
    result = db.get_user(username)
    return result is not None


@app.post("/users/signup")
def create_new_user(req: NewUserRequest):
    exists = db.get_user(req.username)
    if exists:
        raise HTTPException(status_code=400, detail="Username taken")
    hashed = auth.get_password_hash(req.password)
    user = UserInDB(**{
        "username": req.username,
        "full_name": req.full_name,
        "email": req.email,
        "hashed_password": hashed,
        "disabled": False
    })
    # insert and return the generated object id
    result = db.insert_user(user)
    return result.__str__()
    

# token endpoint

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"},)
    access_token_expires = timedelta(minutes=float(os.environ['JWT_EXPIRES']))
    access_token = auth.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
