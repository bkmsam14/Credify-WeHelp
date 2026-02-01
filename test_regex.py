import re

text = "Credit Score: 750"
pattern = r"(?:score|crédit|credit)[\s:]*(\d+)"

match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
if match:
    print(f"Match found: {match.group(1)}")
else:
    print("No match found")
    print(f"Text: {text}")
    print(f"Pattern: {pattern}")
