from fastapi import APIRouter

from models.models import Amount, PIN
from utils.file_handler import load_data, save_data


router = APIRouter()


# Check Balance
@router.get("/balance")
def check_balance():
    data = load_data()

    return {
        "status": "success",
        "balance": data["balance"]
    }


# Deposit Money
@router.post("/deposit")
def deposit_money(data: Amount):
    atm_data = load_data()

    if data.amount <= 0:
        return {
            "status": "error",
            "message": "Invalid amount"
        }

    atm_data["balance"] += data.amount

    atm_data["transactions"].append(
        f"Deposited: ₹{data.amount}"
    )

    save_data(atm_data)

    return {
        "status": "success",
        "message": "Money deposited successfully",
        "new_balance": atm_data["balance"]
    }


# Withdraw Money
@router.post("/withdraw")
def withdraw_money(data: Amount):
    atm_data = load_data()

    if data.amount <= 0:
        return {
            "status": "error",
            "message": "Invalid amount"
        }

    if data.amount > atm_data["balance"]:
        return {
            "status": "error",
            "message": "Insufficient balance"
        }

    atm_data["balance"] -= data.amount

    atm_data["transactions"].append(
        f"Withdrawn: ₹{data.amount}"
    )

    save_data(atm_data)

    return {
        "status": "success",
        "message": "Money withdrawn successfully",
        "remaining_balance": atm_data["balance"]
    }


# Transaction History
@router.get("/transactions")
def transaction_history():
    data = load_data()

    return {
        "status": "success",
        "transactions": data["transactions"]
    }


# Login
@router.post("/login")
def login(data: PIN):
    correct_pin = 1234

    if data.pin == correct_pin:
        return {
            "status": "success",
            "message": "Login successful"
        }

    return {
        "status": "error",
        "message": "Wrong PIN"
    }