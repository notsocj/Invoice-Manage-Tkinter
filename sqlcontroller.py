import sqlite3

# Path to your database file
db_path = "invoice_manager.db"  # Replace with the path to your database file

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add the payment_status field to the invoices table
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN payment_status TEXT;")
        print("Successfully added 'payment_status' field to the 'invoices' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("The 'payment_status' field already exists in the 'invoices' table.")
        else:
            print(f"Error while adding 'payment_status' field: {e}")
            raise

    # Verify the updated structure of the invoices table
    print("\nUpdated structure of the 'invoices' table:")
    cursor.execute("PRAGMA table_info(invoices);")
    columns = cursor.fetchall()

    if not columns:
        print("Table 'invoices' does not exist in the database.")
    else:
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

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

except sqlite3.Error as e:
    print(f"An error occurred: {e}")
    if conn:
        conn.close()