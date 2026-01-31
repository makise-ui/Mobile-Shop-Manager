from core.reporting import ReportGenerator
import pandas as pd
import datetime

def verify():
    print("--- Phase 1 Verification ---")
    data = {
        'unique_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'price': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        'last_updated': [datetime.datetime.now() - datetime.timedelta(days=i) for i in range(10)]
    }
    df = pd.DataFrame(data)
    rpt = ReportGenerator(df)

    # 1. Modulo
    print("\n1. Testing Modulo (ID % 2 == 0)...")
    res = rpt.apply_filters([{'field': 'unique_id', 'operator': 'Modulo', 'value': '2=0'}])
    print(f"   Result IDs: {res['unique_id'].tolist()}")
    if res['unique_id'].tolist() == [2, 4, 6, 8, 10]:
        print("   [PASS]")
    else:
        print("   [FAIL]")

    # 2. Limit
    print("\n2. Testing Limit (3)...")
    res = rpt.apply_limit(df, 3)
    print(f"   Count: {len(res)}")
    if len(res) == 3:
        print("   [PASS]")
    else:
        print("   [FAIL]")

    # 3. Custom Expression
    print("\n3. Testing Custom Expression (price > 800)...")
    res = rpt.apply_custom_expression(df, "price > 800")
    print(f"   Result Prices: {res['price'].tolist()}")
    if res['price'].tolist() == [900, 1000]:
        print("   [PASS]")
    else:
        print("   [FAIL]")
    
    # 4. Date Above
    print("\n4. Testing Date Above (Last 3 days)...")
    # Date 3 days ago
    target = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
    print(f"   Target Date: {target}")
    res = rpt.apply_filters([{'field': 'last_updated', 'operator': 'Above', 'value': target}])
    print(f"   Count: {len(res)}")
    # Should be 0, 1, 2 days ago (3 items)
    if len(res) == 3:
        print("   [PASS]")
    else:
        print("   [FAIL]")

if __name__ == "__main__":
    verify()
