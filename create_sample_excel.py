import pandas as pd
import random

data = {
    'Model Name': ['iPhone 13', 'Samsung S22', 'Pixel 7', 'iPhone 14 Pro', 'OnePlus 11', 'Redmi Note 12'],
    'Variant': ['128GB', '256GB', '128GB', '512GB', '256GB', '64GB'],
    'IMEI Number': [str(random.randint(100000000000000, 999999999999999)) for _ in range(6)],
    'Selling Price': [60000, 55000, 45000, 90000, 48000, 15000],
    'Status':["IN", "IN", "IN", "IN", "IN", "IN"]
}

df = pd.DataFrame(data)
df.to_excel('inventory.xlsx', index=False)
print("Created inventory.xlsx")
