import pdfreader
import os
from pdfreader import PDFDocument, SimplePDFViewer
import sqlite3
import pandas as pd
import re

#add logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(os.path.dirname(__file__),"expense_runner.log"))
logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler())
# set logger level to debug for lof file, and info for console
file_handler.setLevel(logging.DEBUG)
logger.handlers[1].setLevel(logging.INFO)
# set log level to debug for the logger
logger.setLevel(logging.INFO)

'''
Code definitions
'''

# define a function to extract data from the pdf file
def extract_data_from_pdf (file_path):
    logger.info(f"Extracting data from the pdf file {file_path}")
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

        # log the dataframe to the log file
        #logger.debug(df.to_string())

        all_data = join_dataframes(all_data, df)
    return all_data

def store_data_in_database(all_data, database_path):
    conn = sqlite3.connect(database_path)
    # drop the table if it exists
    conn.execute("DROP TABLE IF EXISTS expenses")
    all_data.to_sql("expenses", conn, if_exists="replace", index=False)
    conn.close()
    logger.info("Data stored in the database")
    
def check_data_in_database(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    # log info the number of data in the database
    logger.info(f"Number of data in the database: {len(cursor.fetchall())}")
    logger.debug(cursor.description)
    logger.debug(cursor.fetchall())
    conn.close()

def store_common_patterns(all_data):
    # store the common patterns in  all_data dataframe for column description in a dataframe for whole words and store the number of occurences in additional column called frequency
    all_data["description"] = all_data["description"].str.lower()
    common_patterns = all_data["description"].str.split(expand=True).stack().value_counts()
    common_patterns = common_patterns[common_patterns > 1]
    common_patterns = common_patterns.reset_index()
    common_patterns.columns = ["pattern", "frequency"]
    common_patterns.to_pickle(os.path.join(os.path.dirname(__file__), "common_patterns.pkl"))
    logger.info("Common patterns stored in the pickle file")
    logger.debug(common_patterns.to_string())
    return common_patterns

def store_common_descriptions(all_data):
    # store the common descriptions in the all_data dataframe for column description in a dataframe and store the number of occurences in additional column called frequency
    common_descriptions = all_data["description"].value_counts().reset_index()
    common_descriptions.columns = ["description", "frequency"]
    common_descriptions.to_pickle(os.path.join(os.path.dirname(__file__), "common_descriptions.pkl"))
    logger.info("Common descriptions stored in the pickle file")
    # logger.debug(common_descriptions.to_string())
    return common_descriptions

def check_if_pattern_in_description(description, pattern):
    logger.debug(f"Checking if pattern {pattern} is in description {description.lower()}: {re.search(pattern, description, re.IGNORECASE)}")
    return re.search(pattern, description, re.IGNORECASE) is not None



def set_expense_type(expense_type_file, all_data):
    # read the file expense_type.json from the src folder into expense_type dictionary
    expense_type_data = pd.read_json(expense_type_file, typ="series").to_dict()
    logger.debug(expense_type_data)

    # cycle through the expense_type list for each type and check if for a given type the corresponding string_pattern is in the description column of all_data dataframe["description"]. If it is, add the type to the type column of all_data dataframe["type"]
    for expense_type in expense_type_data["expense_type"]:
        logger.info(f"Checking expense type {expense_type['type']}") 
        for pattern in expense_type["string_pattern"]:
            logger.debug(f"Checking pattern {pattern} to insert type {expense_type['type']}")
            for index, row in all_data.iterrows():
                if check_if_pattern_in_description(row["description"], pattern):
                    all_data.at[index, "type"] = expense_type['type']
    # for any type which is NaN set it to "other"
    all_data["type"].fillna("other", inplace=True)

    # # for each stringe pattern in the expense_type dictionary, check if the pattern is in the all_data dataframe and if it is, add the corresponding "type" to the dataframe
    # expense_type_list =  expense_type_data["expense_type"]
    # for expense_type in expense_type_list:
    #     for pattern in expense_type["string_pattern"]:
    #         logger.debug(f"Checking pattern {pattern} to insert type {expense_type['type']}")
    #         # for each pattern check in all_data["description"] if the pattern is in the description column and if it is, append to type column list the corresponding type 
    #         all_data["type"] = all_data["description"].apply(lambda x: expense_type["type"] if pattern in x else None)
    # # for any type which is NaN set it to "other"
    # all_data["type"].fillna("other", inplace=True)
    return all_data


def main() -> None:
    expenses_dir = os.path.join(os.path.dirname(__file__), "..", "cc")  
    database_path = os.path.join(os.path.dirname(__file__), "expenses.db")
    expense_type_file = os.path.join(os.path.dirname(__file__), "expense_type.json")
    # cycle thorugh all the pdf files in the file_path folder
    logger.info(f"Extracting data from the pdf files in folder \n{expenses_dir}")
    all_data = cycle_through_files(expenses_dir)

    # store the all_data dataframe in a pickle file
    all_data.to_pickle(os.path.join(os.path.dirname(__file__), "all_data.pkl"))

    # store the all_data dataframe in a database
    store_data_in_database(all_data, database_path)
    check_data_in_database(database_path)

    # load the pickle file into the all_data dataframe
    all_data = pd.read_pickle(os.path.join(os.path.dirname(__file__), "all_data.pkl"))
    all_data = set_expense_type(expense_type_file, all_data)
    # common_patterns = store_common_patterns(all_data)
    # common_descriptions = store_common_descriptions(all_data)
    logger.info(all_data.to_string())

if __name__ == "__main__":
    main()
