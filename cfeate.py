import pandas as pd
import random

data = {
    'Model Name': [
        'iPhone 15',
        'iPhone 14',
        'Samsung Galaxy S23',
        'Samsung Galaxy A54',
        'Pixel 8',
        'OnePlus 12',
        'OnePlus Nord CE 3',
        'Redmi Note 13 Pro',
        'Realme GT Neo 3',
        'Vivo V29'
    ],
    'Variant': [
        '128GB',
        '256GB',
        '256GB',
        '128GB',
        '128GB',
        '256GB',
        '128GB',
        '256GB',
        '256GB',
        '128GB'
    ],
    'IMEI Number': [
        str(random.randint(100000000000000, 999999999999999))
        for _ in range(10)
    ],
    'Selling Price': [
        79999,
        69999,
        74999,
        38999,
        75999,
        64999,
        29999,
        27999,
        35999,
        36999
    ],
    'Status': [
        'IN','IN','IN','IN','IN','IN','OUT','IN','IN','OUT'
    ]
}

df = pd.DataFrame(data)
df.to_excel('inventory.xlsx', index=False)

print("Created inventory.xlsx with 10 mobile phones 🔥")
