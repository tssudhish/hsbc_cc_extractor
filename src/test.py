import re

data = [
"03 Jun 24 01 Jun 24 ))) GERMAN DONER KEBAB     CHELTENHAM GL 82.50",
"03 Jun 24 01 Jun 24 PAYPAL *SOLY           07702180024 3,750.85",
"03 Jun 24 02 Jun 24 AWS EMEA               aws.amazon.co LUX 0.96"]

# extract the data from data to get the following output
# data_extract =  [["03 Jun 24","01 Jun 24", "GERMAN DONER KEBAB     CHELTENHAM GL", 82.50],
#  ["03 Jun 24","01 Jun 24", "PAYPAL *SOLY           07702180024", 3750.85],
#  ["03 Jun 24","02 Jun 24", "AWS EMEA               aws.amazon.co LUX", 0.96]]

data_extract = []
for item in data:
    match = re.match(r"(\d{2} \w{3} \d{2}) (\d{2} \w{3} \d{2}) (.+?)\s+(\d+\.\d+)", item)
    if match:
        data_extract.append([match.group(1), match.group(2), match.group(3), float(match.group(4))])


print(data_extract)