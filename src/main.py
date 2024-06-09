import pdfreader
import os
from pdfreader import PDFDocument, SimplePDFViewer
import sqlite3
import pandas as pd
import re

'''
Code definitions
'''

# define a function to extract data from the pdf file
def extract_data_from_pdf (file_path):
    print(f"Extracting data from the pdf file {file_path}")
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

    dates = re.findall(r"\d{2} [A-Z][a-z]{2} \d{2}\s\d{2} [A-Z][a-z]{2} \d{2}", combined_strings)
    new_line_patterns = dates +  ["Sheet number", "Summary Of", "Card number", "Your Rewards"]
    for elem in new_line_patterns:
        combined_strings = combined_strings.replace(elem, "\n" + elem)

    combined_strings = re.sub(r"\n+", "\n", combined_strings)

    # remove all the lines that are not containing elements of dates
    combined_strings = "\n".join([line for line in combined_strings.split("\n") if any(date in line for date in dates)])

    return combined_strings


def extract_expense(processed_data):
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

# define a function to create a pandas dataframe from the extracted data
def create_dataframe(extract_data):
    df = pd.DataFrame(extract_data)
    return df

# define a function to join the dataframe to an existing dataframe all_data
def join_dataframes(all_data, df):
    all_data = pd.concat([all_data, df], ignore_index=True)
    return all_data



def cycle_through_files(expenses_dir):
    all_data = pd.DataFrame()
    # cycle thorugh all the pdf files in the file_path folder
    for file_name in os.listdir(expenses_dir):
        if not file_name.endswith(".pdf"):
            continue
        file_path = os.path.join(expenses_dir, file_name)
        # extract the name  from the file_name without the extension
        name = os.path.splitext(file_name)[0]
        all_strings = extract_data_from_pdf(file_path)        
        processed_data = process_data(all_strings)
        extract_data = extract_expense( processed_data)
        df = create_dataframe(extract_data)
        # add the name column to the dataframe df
        df["name"] = name
        all_data = join_dataframes(all_data, df)
    return all_data

def store_data_in_database(all_data, database_path):
    conn = sqlite3.connect(database_path)
    # drop the table if it exists
    conn.execute("DROP TABLE IF EXISTS expenses")
    all_data.to_sql("expenses", conn, if_exists="replace", index=False)
    conn.close()
    print("Data stored in the database")

    # check the data stored in the database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    print(cursor.fetchall())
    conn.close()
def check_data_in_database(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    print(cursor.fetchall())
    conn.close()

def main() -> None:
    expenses_dir = os.path.join(os.path.dirname(__file__), "cc")  
    database_path = os.path.join(os.path.dirname(__file__), "expenses.db")
    # cycle thorugh all the pdf files in the file_path folder
    print(f"Extracting data from the pdf files in folder \n{expenses_dir}")
    all_data = cycle_through_files(expenses_dir)

    
    store_data_in_database(all_data, database_path)
    # check_data_in_database(database_path)



if __name__ == "__main__":
    main()
