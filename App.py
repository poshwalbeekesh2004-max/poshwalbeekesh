from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
import os
import sqlite3
from datetime import datetime


app = FastAPI(title="ATM Banking API")


# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("atm.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    pin INTEGER,
    balance REAL
)
""")

conn.commit()


# Add default user only if database is empty
cursor.execute("SELECT * FROM users")

if cursor.fetchone() is None:
    cursor.execute("""
    INSERT INTO users (name, pin, balance)
    VALUES (?, ?, ?)
    """, ("Bikesh", 1234, 1000.0))

    conn.commit()


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def get_balance_from_db():
    cursor.execute(
        "SELECT balance FROM users WHERE id = 1"
    )

    user = cursor.fetchone()

    if user:
        return user[0]

    raise ValueError("User not found")


def update_balance_in_db(new_balance):
    cursor.execute(
        "UPDATE users SET balance = ? WHERE id = 1",
        (new_balance,)
    )

    conn.commit()


def get_pin_from_db():
    cursor.execute(
        "SELECT pin FROM users WHERE id = 1"
    )

    user = cursor.fetchone()

    if user:
        return user[0]

    raise ValueError("User not found")


def update_pin_in_db(new_pin):
    cursor.execute(
        "UPDATE users SET pin = ? WHERE id = 1",
        (new_pin,)
    )

    conn.commit()


# =========================================================
# REQUEST MODELS / VALIDATION
# =========================================================

class Amount(BaseModel):
    amount: float = Field(
        gt=0,
        description="Amount must be greater than 0"
    )


class PinData(BaseModel):
    pin: int = Field(
        ge=1000,
        le=9999,
        description="PIN must be exactly 4 digits"
    )


class ChangePinData(BaseModel):
    old_pin: int = Field(
        ge=1000,
        le=9999
    )

    new_pin: int = Field(
        ge=1000,
        le=9999
    )


# =========================================================
# ATM CLASS
# =========================================================

class ATM:

    def __init__(self):

        self.file_name = "atm_data.json"

        if not os.path.exists(self.file_name):

            self.data = {
                "balance": get_balance_from_db(),
                "transactions": []
            }

            self.save_data()

        else:
            self.load_data()


    # -----------------------------------------------------
    # Load JSON
    # -----------------------------------------------------

    def load_data(self):

        try:

            with open(self.file_name, "r") as file:
                self.data = json.load(file)

            # Make sure transactions exists
            if "transactions" not in self.data:
                self.data["transactions"] = []

        except (json.JSONDecodeError, FileNotFoundError):

            self.data = {
                "balance": get_balance_from_db(),
                "transactions": []
            }

            self.save_data()


    # -----------------------------------------------------
    # Save JSON
    # -----------------------------------------------------

    def save_data(self):

        with open(self.file_name, "w") as file:

            json.dump(
                self.data,
                file,
                indent=4
            )


    # -----------------------------------------------------
    # Add Transaction
    # -----------------------------------------------------

    def add_transaction(self, transaction_type, amount):

        transaction = {

            "type": transaction_type,

            "amount": amount,

            "time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        self.data["transactions"].append(
            transaction
        )

        self.save_data()


    # -----------------------------------------------------
    # Check Balance
    # -----------------------------------------------------

    def check_balance(self):

        balance = get_balance_from_db()

        self.data["balance"] = balance
        self.save_data()

        return balance


    # -----------------------------------------------------
    # Deposit
    # -----------------------------------------------------

    def deposit(self, amount):

        if amount <= 0:
            raise ValueError(
                "Amount must be greater than 0"
            )

        current_balance = get_balance_from_db()

        new_balance = current_balance + amount

        update_balance_in_db(new_balance)

        self.data["balance"] = new_balance

        self.add_transaction(
            "Deposit",
            amount
        )

        return new_balance


    # -----------------------------------------------------
    # Withdraw
    # -----------------------------------------------------

    def withdraw(self, amount):

        if amount <= 0:
            raise ValueError(
                "Amount must be greater than 0"
            )

        current_balance = get_balance_from_db()

        if amount > current_balance:
            raise ValueError(
                "Insufficient balance"
            )

        new_balance = current_balance - amount

        update_balance_in_db(new_balance)

        self.data["balance"] = new_balance

        self.add_transaction(
            "Withdraw",
            amount
        )

        return new_balance


    # -----------------------------------------------------
    # Transaction History
    # -----------------------------------------------------

    def transaction_history(self):

        self.load_data()

        return self.data["transactions"]


    # -----------------------------------------------------
    # Check PIN
    # -----------------------------------------------------

    def check_pin(self, pin):

        correct_pin = get_pin_from_db()

        if pin != correct_pin:

            raise ValueError(
                "Incorrect PIN"
            )

        return True


    # -----------------------------------------------------
    # Change PIN
    # -----------------------------------------------------

    def change_pin(self, old_pin, new_pin):

        if old_pin == new_pin:

            raise ValueError(
                "New PIN must be different from old PIN"
            )

        correct_pin = get_pin_from_db()

        if old_pin != correct_pin:

            raise ValueError(
                "Incorrect old PIN"
            )

        if new_pin < 1000 or new_pin > 9999:

            raise ValueError(
                "PIN must be exactly 4 digits"
            )

        update_pin_in_db(new_pin)

        return "PIN changed successfully"


# =========================================================
# CREATE ATM OBJECT
# =========================================================

atm = ATM()


# =========================================================
# API ROUTES
# =========================================================


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "Welcome to ATM Banking API"
    }


# ---------------------------------------------------------
# BALANCE
# ---------------------------------------------------------

@app.get("/balance")
def get_balance():

    try:

        balance = atm.check_balance()

        return {
            "balance": balance
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------------------------------------------------
# DEPOSIT
# ---------------------------------------------------------

@app.post("/deposit")
def deposit_money(data: Amount):

    try:

        new_balance = atm.deposit(
            data.amount
        )

        return {

            "message":
                "Money deposited successfully",

            "amount":
                data.amount,

            "balance":
                new_balance
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# ---------------------------------------------------------
# WITHDRAW
# ---------------------------------------------------------

@app.post("/withdraw")
def withdraw_money(data: Amount):

    try:

        new_balance = atm.withdraw(
            data.amount
        )

        return {

            "message":
                "Money withdrawn successfully",

            "amount":
                data.amount,

            "balance":
                new_balance
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# ---------------------------------------------------------
# TRANSACTION HISTORY
# ---------------------------------------------------------

@app.get("/transactions")
def get_transactions():

    try:

        return {

            "transactions":
                atm.transaction_history()
        }

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch transaction history"
        )


# ---------------------------------------------------------
# CHECK PIN
# ---------------------------------------------------------

@app.post("/check-pin")
def check_pin(data: PinData):

    try:

        atm.check_pin(
            data.pin
        )

        return {

            "message":
                "PIN is correct"
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ---------------------------------------------------------
# CHANGE PIN
# ---------------------------------------------------------

@app.post("/change-pin")
def change_pin(data: ChangePinData):

    try:

        result = atm.change_pin(
            data.old_pin,
            data.new_pin
        )

        return {
            "message": result
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )