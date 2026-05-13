with open('backend/static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    "                createTagGroup(wsLeftColumn, 'Increment', 'wsIncrement', 'Enter increment...', true, { singleValueOnly: true, numericOnly: true });\n"
    "                createTagGroup(wsLeftColumn, 'Bank Name', 'wsBankNameCompany', 'Enter bank name...', true);"
)
new = (
    "                createTagGroup(wsLeftColumn, 'Increment', 'wsIncrement', 'Enter increment...', true, { singleValueOnly: true, numericOnly: true });\n"
    "                createTagGroup(wsLeftColumn, 'Account Number End', 'wsAccountNumberEnd', 'Enter end number...', true, { singleValueOnly: true, numericOnly: true });\n"
    "                createTagGroup(wsLeftColumn, 'Bank Name', 'wsBankNameCompany', 'Enter bank name...', true);"
)

if old in content:
    content = content.replace(old, new, 1)
    with open('backend/static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('DONE - field inserted')
else:
    print('NOT FOUND - old string not in file')

