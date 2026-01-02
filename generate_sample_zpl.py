def calculate_barcode_x(data, column_center_x, module_width=2):
    # 35 modules overhead (Start + Checksum + Stop) + 11 per char
    total_modules = 35 + (11 * len(str(data)))
    barcode_width_dots = total_modules * module_width
    start_x = column_center_x - (barcode_width_dots / 2)
    return int(start_x)

items = [
    {"id": 101, "model": "Samsung Galaxy A54 5G", "specs": "8/128 GB", "price": 32000},
    {"id": 102, "model": "Motorola Moto G54 Power", "specs": "12/256 GB", "price": 18500},
    {"id": 103, "model": "Vivo V27 Pro", "specs": "8/128 GB", "price": 35000},
    {"id": 104, "model": "iPhone 15 Blue", "specs": "128 GB", "price": 72000}
]

zpl_output = ""

# Process in pairs
for i in range(0, len(items), 2):
    item1 = items[i]
    item2 = items[i+1] if i+1 < len(items) else None
    
    zpl_output += "^XA^PW830^LL176\n"
    
    def get_fields(item, x_offset):
        uid = str(item['id'])
        # Center of this column is x_offset + 200 (half of 400 width)
        center_x = x_offset + 200
        bc_x = calculate_barcode_x(uid, center_x)
        
        return f"""
^FO{x_offset+0},5^A0N,28,28
^FB400,1,0,C,0^FD4bros mobile^FS

^FO{bc_x},35^BY2,2,40^BCN,40,N,N,N
^FD{uid}^FS

^FO{x_offset+0},80^A0N,22,22
^FB400,1,0,C,0^FD{uid}^FS

^FO{x_offset+10},105^A0N,22,22
^FB280,2,0,L,0^FD{item['model']}^FS

^FO{x_offset+10},145^A0N,22,22
^FB200,1,0,L,0^FD{item['specs']}^FS

^FO{x_offset+150},140^A0N,30,30
^FB230,1,0,R,0^FDRs. {item['price']:,}^FS
"""

    zpl_output += get_fields(item1, 0)
    
    if item2:
        # Second label starts at 416 (approx 52mm)
        zpl_output += get_fields(item2, 416)
        
    zpl_output += "^XZ\n"

with open("sample_precise_4.zpl", "w") as f:
    f.write(zpl_output)

print(zpl_output)
