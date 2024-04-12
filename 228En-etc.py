# 228EN-etc
import os
import sqlite3
import csv

conn = None
cursor = None
db_path = None

Rate_DICT = {'HCP': 1.6, 'NDIS': 1.0, 'STRC': 1.6, 'FR': 1.6, 'OPC': 0.0}


def create_connection(db_path):
    global conn, cursor
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


def create_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pcw_data (
            pcw_id TEXT,
            client_name TEXT,
            mileage INTEGER,
            parking_fee INTEGER,
            rate REAL,
            rate_name TEXT,
            total_mileage INTEGER,
            total_parking_fee INTEGER,
            total_income REAL,
            client_total_mileage INTEGER,
            client_total_parking_fee INTEGER,
            client_total_cost REAL,
            PRIMARY KEY (pcw_id, client_name)
        )
    ''')
    conn.commit()


def add_data(pcw_id, client_name, mileage, parking_fee, rate, rate_name):
    cursor.execute('''
        INSERT OR REPLACE INTO pcw_data (pcw_id, client_name, mileage, parking_fee, rate, rate_name)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (pcw_id, client_name, mileage, parking_fee, rate, rate_name))
    conn.commit()

def update_data(pcw_id, client_name, mileage, parking_fee, rate, rate_name):
    cursor.execute('''
        UPDATE pcw_data
        SET mileage = ?, parking_fee = ?, rate = ?, rate_name = ?
        WHERE pcw_id = ? AND client_name =?
    ''', (mileage, parking_fee, rate, rate_name, pcw_id, client_name))
    conn.commit()
    calculate_income(pcw_id)
    calculate_client_summary(client_name)
    display_data(pcw_id, client_name)
    print(f"\n The data for {pcw_id} and {client_name} has been updated.")

def delete_data(pcw_id, client_name):
    cursor.execute('''
        DELETE FROM pcw_data
        WHERE pcw_id = ? AND client_name = ?
    ''', (pcw_id, client_name))
    conn.commit()
    calculate_income(pcw_id)
    calculate_client_summary(client_name)

    
def calculate_income(pcw_id):
    # 首先更新 total_mileage 和 total_parking_fee
    cursor.execute('''
        UPDATE pcw_data
        SET total_mileage = (SELECT SUM(mileage) FROM pcw_data WHERE pcw_id=?),
            total_parking_fee = (SELECT SUM(parking_fee) FROM pcw_data WHERE pcw_id=?)
        WHERE pcw_id=?
    ''', (pcw_id, pcw_id, pcw_id))
    conn.commit()

    # 然後使用新的 total_mileage 和 total_parking_fee 計算 total_income
    cursor.execute('''
        UPDATE pcw_data
        SET total_income = ROUND((total_mileage * 0.96 + total_parking_fee),2)
        WHERE pcw_id=?
    ''', (pcw_id,))
    conn.commit()


def calculate_client_summary(client_name):
    # 首先更新 client_total_mileage 和 client_total_parking_fee
    cursor.execute('''
        UPDATE pcw_data
        SET client_total_mileage = (SELECT SUM(mileage) FROM pcw_data WHERE client_name=?),
            client_total_parking_fee = (SELECT SUM(parking_fee) FROM pcw_data WHERE client_name=?)
        WHERE client_name=?
    ''', (client_name, client_name, client_name))
    conn.commit()

    # 然後使用新的 client_total_mileage 和 client_total_parking_fee 計算 client_total_cost
    cursor.execute('''
        UPDATE pcw_data
        SET client_total_cost = ROUND((client_total_mileage * rate + client_total_parking_fee),2)
        WHERE client_name=?
    ''', (client_name,))
    conn.commit()


def display_summary():
    cursor.execute('SELECT * FROM pcw_data')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        print('\n')


def export_to_csv():
    global db_path #声明使用全局变量
    conn = sqlite3.connect(db_path)  # 连接到 SQLite 数据库
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pcw_data")  # 从表中检索数据

    #从db_path中提取文件夹路径
    folder_path = os.path.dirname(db_path)

    #构造csv文件的完整路径
    csv_file_path = os.path.join(folder_path, 'data.csv')

    with open(csv_file_path, 'w', newline='') as csvfile:  # 打开 CSV 文件
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([i[0] for i in cursor.description])  # 写入标题行
        csv_writer.writerows(cursor)  # 写入数据行

    conn.close()
    print(f"数据已成功导出到 {csv_file_path} 文件中。")


def input_pcw_data():
    while True:
        pcw_id = input("\n Please enter the employee's ID (Enter -1 to return to the menu):").upper()
        if pcw_id == '-1':
            break

        while True:
            client_name = input("\n Please enter the client's name (Enter -1 to return to the menu):")
            if client_name == '-1':
                return

            print("\n What do you want to do?")
            print("1. Add new data")
            print("2. Update existing data")
            print("3. Delete date")
            print("4. Return to the previous menu")
            option = input("Enter your choice (1/2/3/4):")

            if option == '1':
                mileage = get_mileage_input()
                parking_fee = get_parking_fee_input()
                rate, rate_name = get_rate_input()
                add_data(pcw_id, client_name, mileage, parking_fee, rate, rate_name)
                calculate_income(pcw_id)
                calculate_client_summary(client_name)
                display_data(pcw_id, client_name)
                print(f"\n The data for {pcw_id} adn {client_name} has been added.")

            elif option == '2':
                mileage = get_mileage_input()
                parking_fee = get_parking_fee_input()
                rate, rate_name = get_rate_input()
                update_data(pcw_id, client_name, mileage, parking_fee, rate, rate_name)
                

            elif option == '3':
                confirm = input(f"\n Are you sure you want to delete the data for {pcw_id} and {client_name}? (y/n)")
                if confirm.lower() == 'y':
                    delete_data(pcw_id, client_name)
                    print(f"\n The data for {pcw_id} and {client_name} has been deleted.")

            elif option == '4':
                continue

            else:
                print("\n Invalid option, please try again.")
                
def get_mileage_input():
    mileage_list = []
    while True:
        try:
            mileage = float(input("\n Please enter the mileage (Enter -1 to finish input):"))
            if mileage == -1:
                break
            mileage_list.append(mileage)
        except ValueError:
            print("\n Invalid input, please try again!\n")
            continue

    mileage_list_confirm = []
    while True:
        try:
            print("\n Please enter the mileage again for confirmation:")
            for i in range(len(mileage_list)):
                mileage = float(input(f"\n The {i + 1} mileage:"))
                mileage_list_confirm.append(mileage)
            break
        except ValueError:
            print("\n Invalid input, please try again!\n")
            mileage_list_confirm = []
            continue

    if mileage_list == mileage_list_confirm:
        return sum(mileage_list)
    else:
        print("\n The mileage input does not match. Please enter again!\n")
        return get_mileage_input()

def get_parking_fee_input():
    parking_fee_list = []
    while True:
        try:
            parking_fee = float(input("\n Please enter the parking fee (Enter -1 to finish input):"))
            if parking_fee == -1:
                break
            parking_fee_list.append(parking_fee)
        except ValueError:
            print("\n Invalid input, please try again!\n")
            continue

    parking_fee_list_confirm = []
    while True:
        try:
            print("\n Please enter the parking fee again for confirmation:")
            for i in range(len(parking_fee_list)):
                fee = float(input(f"\n The {i + 1} parking fee:"))
                parking_fee_list_confirm.append(fee)
            break
        except ValueError:
            print("\n Invalid input, please try again!\n")
            parking_fee_list_confirm = []
            continue

    if parking_fee_list == parking_fee_list_confirm:
        return sum(parking_fee_list)
    else:
        print("\n The parking fee input does not match. Please enter again!\n")
        return get_parking_fee_input()

def get_rate_input():
    while True:
        rate_option = input("\n Please select the rate(HCP/NDIS/STRC/FR/OPC):").upper()
        if rate_option == 'OPC':
            rate = float(input("Please input the rate:"))
            rate_name = 'OPC'
            return rate, rate_name
        elif rate_option in Rate_DICT:
            rate = Rate_DICT[rate_option]
            rate_name = rate_option
            return rate, rate_name
        else:
            print("\n Please select from tha above items!\n")

def display_data(pcw_id, client_name):
    print(
        f"\n {pcw_id}'s data for this month: The total mileage is {cursor.execute('SELECT total_mileage FROM pcw_data WHERE pcw_id=?', (pcw_id,)).fetchone()[0]} KM, the total parking fee is {cursor.execute('SELECT total_parking_fee FROM pcw_data WHERE pcw_id=?', (pcw_id,)).fetchone()[0]} AUD, and the total income is {cursor.execute('SELECT total_income FROM pcw_data WHERE pcw_id=?', (pcw_id,)).fetchone()[0]} AUD."
        )
    print(
        f"\n {client_name} is a client of {cursor.execute('SELECT rate_name FROM pcw_data WHERE client_name=?', (client_name,)).fetchone()[0]}. The data for this month: The total mileage is {cursor.execute('SELECT client_total_mileage FROM pcw_data WHERE client_name=?', (client_name,)).fetchone()[0]} KM, the total parking fee is {cursor.execute('SELECT client_total_parking_fee FROM pcw_data WHERE client_name=?', (client_name,)).fetchone()[0]} AUD, and the total cost is {cursor.execute('SELECT client_total_cost FROM pcw_data WHERE client_name=?', (client_name,)).fetchone()[0]} AUD."
        )


def main():
    global db_path #声明使用全局变量
    db_path = input("Please enter the path to save the database file (e.g. C:/Users/username/Desktop/database.db): ")

    # 如果文件夹不存在，则创建文件夹
    folder_path = os.path.dirname(db_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    create_connection(db_path)
    create_table()

    print('\n')


    while True:
        try:
            print("1,Data Admin")
            print("2,Search PCW data")
            print("3,Search Client data")
            print("4,Display summary ")
            print("5,Save and exit")
            print("6,Export to csv")

            choice = input("\n Please select operation (1/2/3/4/5/6):")

            if choice == '1':
                input_pcw_data()

            elif choice == '2':
                pcw_id = input("Please enter the employee's ID:").upper()
                calculate_income(pcw_id)
                print(
                    f"\n {pcw_id}'s data for this month: The total mileage is {cursor.execute('SELECT total_mileage FROM pcw_data WHERE pcw_id=?', (pcw_id,)).fetchone()[0]} KM, the total parking fee is {cursor.execute('SELECT total_parking_fee FROM pcw_data WHERE pcw_id=?', (pcw_id,)).fetchone()[0]} AUD, and the total income is {cursor.execute('SELECT total_income FROM pcw_data WHERE pcw_id=?', (pcw_id,)).fetchone()[0]} AUD.\n")


            elif choice == '3':
                client_name = input("Please enter the client's name:")
                calculate_client_summary(client_name)
                print(
                    f"\n {client_name} is a client of {cursor.execute('SELECT rate_name FROM pcw_data WHERE client_name=?', (client_name,)).fetchone()[0]}. The data for this month: The total mileage is {cursor.execute('SELECT client_total_mileage FROM pcw_data WHERE client_name=?', (client_name,)).fetchone()[0]} KM, the total parking fee is {cursor.execute('SELECT client_total_parking_fee FROM pcw_data WHERE client_name=?', (client_name,)).fetchone()[0]} AUD, and the total cost is {cursor.execute('SELECT client_total_cost FROM pcw_data WHERE client_name=?', (client_name,)).fetchone()[0]} AUD.\n")


            elif choice == '4':
                display_summary()

            elif choice == '5':
                conn.close()
                break

            elif choice == '6':
                export_to_csv()
                print(f"\n The data has been exported.\n")

        except Exception as e:
            print(f"\n Invalid command {e}\n")
            print("Please select again!\n")


if __name__ == "__main__":
    main()
