import pdfreader
import os
from pdfreader import PDFDocument, SimplePDFViewer

file_path = os.path.join(os.path.dirname(__file__), "cc", "2024-04-29_Statement.pdf")
database_path = os.path.join(os.path.dirname(__file__), "expenses.db")
def extract_data_from_pdf (file_path):
    all_strings = []
    with open(file_path, "rb") as fd:
        doc = PDFDocument(fd)
        viewer = SimplePDFViewer(fd)

        for canvas in viewer:
            page_images = canvas.images
            page_forms = canvas.forms
            page_text = canvas.text_content
            page_inline_images = canvas.inline_images
            page_strings = canvas.strings
            all_strings.extend(page_strings)
    return all_strings

def process_data(all_strings):
    combined_strings = " ".join(all_strings)

    import re
    dates = re.findall(r"\d{2} [A-Z][a-z]{2} \d{2}\s\d{2} [A-Z][a-z]{2} \d{2}", combined_strings)
    new_line_patterns = dates +  ["Sheet number", "Summary Of", "Card number", "Your Rewards"]
    for elem in new_line_patterns:
        combined_strings = combined_strings.replace(elem, "\n" + elem)

    combined_strings = re.sub(r"\n+", "\n", combined_strings)

    # remove all the lines that are not containing elements of dates
    combined_strings = "\n".join([line for line in combined_strings.split("\n") if any(date in line for date in dates)])

    return combined_strings


def extract_expense(processed_data):
    import re
    expense_data = []
    # create a databased to store the extracted data
    for line in processed_data.split("\n"):
        #print(line)
        # use the pattern /(\d+\s\w*\s\d\d)\s(\d+\s\w*\s\d\d)\s(.*)\s(\d+[.]\d+)$/gm to extract posting date, purchase date, description and amount from line
        
        pattern = (
            r"(\d{2} [A-Z][a-z]{2} \d{2})\s"
            r"(\d{2} [A-Z][a-z]{2} \d{2})\s"
            r"(.*?)\s"
            r"(\d+[.]\d+)"
        )
        match = re.match(pattern, line)
        if match is None:
            continue
        posting_date, purchase_date, description, amount = match.groups()
        # convert the posting_date and purchase_date to a standard format
        posting_date = re.sub(r"(\d{2}) ([A-Z][a-z]{2}) (\d{2})", r"\1-\2-20\3", posting_date)
        purchase_date = re.sub(r"(\d{2}) ([A-Z][a-z]{2}) (\d{2})", r"\1-\2-20\3", purchase_date)
        
        expense_data.append({"posting_date" : posting_date, 
                             "purchase_date" : purchase_date, 
                             "description" : description, 
                             "amount" : amount})
    return expense_data


# insert the extracted data into the database
def insert_data_to_database(name, extract_data):
    import sqlite3
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    # delete existing table
    cursor.execute("DROP TABLE IF EXISTS expenses")
    # create a table to store the extracted data with posting date, purchaase date, description and amount
    # add a unique id for each row

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
        expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        posting_date DATE, 
        purchase_date DATE, 
        description TEXT, 
        amount REAL)"""
    )
    # insert the extracted data into the database
    for data in extract_data:
        cursor.execute(
            "INSERT INTO expenses (file_name, posting_date, purchase_date, description, amount) VALUES (?, ?, ?, ?, ?)",
            (name, data["posting_date"], data["purchase_date"], data["description"], data["amount"]),
        )
    conn.commit()
    conn.close()

# define a function to insert a column expense type into the database
def additional_columns(expense_type):
    import sqlite3
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE expenses ADD COLUMN expense_type TEXT")
    cursor.execute("UPDATE expenses SET expense_type = ?", (expense_type,))
    conn.commit()
    conn.close()

def check_database() -> None:

    import sqlite3
    # check the database for the extracted data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    for row in cursor.fetchall():
        print(row)
    conn.close()


def main() -> None:
    # extract the file_name from the path file_path
    file_name = os.path.basename(file_path)
    # extract the name  from the file_name without the extension
    name = os.path.splitext(file_name)[0]

    all_strings = extract_data_from_pdf(file_path)        
    processed_data = process_data(all_strings)
    extract_data = extract_expense( processed_data)
    insert_data_to_database(name, extract_data)
    check_database()


if __name__ == "__main__":
    main()
