import models
from functions import generate_clients, generate_merchants, generate_transactions, save_to_csv, print_centered, \
    remove_all_files

if __name__ == "__main__":
    clients = generate_clients(20)
    merchants = generate_merchants(3)
    transactions = generate_transactions(100, clients, merchants)

    print_centered("Модели созданы!")

    remove_all_files()

    save_to_csv("clients.csv",clients, ["client_id","gender","age"])
    print_centered("Файл clients.csv успешно создан!")

    save_to_csv("merchants.csv", merchants, ["merchant_id","latitude","longitude"])
    print_centered("Файл merchants.csv успешно создан!")

    save_to_csv("transactions.csv", transactions,
                ["transaction_id", "merchant_id", "client_id", "transaction_dttm", "transaction_amt"])
    print_centered("Файл transactions.csv успешно создан!")