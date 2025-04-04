import sqlite3

# Path to your database file
db_path = "invoice_manager.db"  # Replace with the path to your database file

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check the fields of the invoices and invoice_items tables
    tables_to_check = ["invoices", "invoice_items"]
    for table_name in tables_to_check:
        print(f"\nTable: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"Table {table_name} does not exist in the database.")
            continue
        
        print("Fields:")
        for column in columns:
            col_name = column[1]  # Column name
            col_type = column[2]  # Data type
            not_null = "NOT NULL" if column[3] == 1 else "NULL"  # Not null constraint
            default_value = f"DEFAULT {column[4]}" if column[4] is not None else ""  # Default value
            primary_key = "PRIMARY KEY" if column[5] == 1 else ""  # Primary key
            print(f" - {col_name} ({col_type}) {not_null} {default_value} {primary_key}".strip())

    # Optional: Verify all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\nAll tables in the database:")
    for table in tables:
        print(table[0])

    # Close the connection
    conn.close()

except sqlite3.Error as e:
    print(f"An error occurred: {e}")