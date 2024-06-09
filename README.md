# Expense Extractor 

This code extracts expenses from credit card statements of HSBC Bank.

## How to run the code?

Put all your expense statements (pdf files) into the folder 'cc' at the same level as the code.

i.e. at the same level as 'src' folder

e.g/

```

/Python
|
|--> src
|
|--> cc/
      |
      |--> Put pdf files here.
```
run the code `python main.py`


## Patterns used

To extract expenses from the credit card statements in the PDF file, the following pattern is checked from the statement:

```markdown
| posting_date | purchase_date | description | amount |
|--------------|------------------|-------------|--------|
|              |                  |             |        |
|              |                  |             |        |
|              |                  |             |        |
```

## Modules used in the code

The following modules are used in the code:

- `os`: Used for interacting with the operating system, specifically for file operations.
- `re`: Used for regular expression matching and operations.
- `PyPDF2`: Used for extracting text from PDF files.
- `pandas`: Used for data manipulation and analysis.
- `tabulate`: Used for creating formatted tables from data.
- `datetime`: Used for working with dates and times.
- `argparse`: Used for parsing command-line arguments.
- `logging`: Used for logging messages during the execution of the code.
- `sys`: Used for interacting with the Python interpreter.
- `sqlite3`: temporarily used to create sql database for the same information.
- `matplotlib`: Used for creating visualizations and plots.
- `json`: Used for working with JSON data.

