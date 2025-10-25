import csv
import glob
import random
import directories
import os
from datetime import datetime, timedelta
from typing import Optional, List
from models import Client, Merchant, Transaction
import shutil

# Generate clients for sample csv
def generate_clients(n: int) -> List[Client]:
    genders = ['M', 'F']
    return [
        Client(
            client_id=i,
            gender=random.choice(genders),
            age=random.randint(16, 70)
        )
        for i in range(1, n + 1)
    ]

# Generate stores for sample data csv
def generate_merchants(n: int) -> List[Merchant]:
    return [
        Merchant(
            merchant_id=i,
            latitude=round(random.uniform(55.0,56.0), 6),
            longitude=round(random.uniform(37.0,38.0), 6),
            mcc_cd=random.choice([5411,5732,5812,5921,5999])
        )
        for i in range(1, n+1)
    ]

# Generate transactions for sample data csv
def generate_transactions(n:int, clients: List[Client], merchants: List[Merchant]) -> List[Transaction]:
    transactions = []
    start_date = datetime(2020,1,1)
    for i in range(1, n+1):
        client = random.choice(clients)
        merchant = random.choice(merchants)
        transaction_dttm = start_date + timedelta(days=random.randint(0, 1095))
        transaction_amt = round(random.uniform(5,500), 2)
        transactions.append(Transaction(
            transaction_id=i,
            merchant_id=merchant.merchant_id,
            client_id=client.client_id,
            transaction_dttm=transaction_dttm,
            transaction_amt=transaction_amt
        ))
    return transactions

# Saving generated data with csv type
def save_to_csv(filename: str, objects: List[object], fieldnames: List[str], folder: str = directories.DATA_DIR):
    path = os.path.join(folder, filename)
    remove_all_files()
    with open(path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for obj in objects:
            writer.writerow({k: getattr(obj,k) for k in fieldnames})

# Pretty print for logs
def print_centered(text: str, fill: str = "-"):
    width = shutil.get_terminal_size().columns
    print(f"{text:{fill}^{width}}")

# Clean directory
def remove_all_files(folder: str = directories.DATA_DIR):
    files = glob.glob(os.path.join(folder, "*"))
    for file in files:
        os.remove(file)
        print_centered(f"Удалён: {file}")
    if not files:
        print_centered(f"Директория пуста")