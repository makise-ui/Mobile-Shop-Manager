from PIL import Image, ImageDraw, ImageFont
import os

ICON_DIR = "assets/icons"
os.makedirs(ICON_DIR, exist_ok=True)

ICONS = {
    "plus-lg.png": "+",
    "printer.png": "P",
    "trash.png": "x",
    "arrow-clockwise.png": "R",
    "filter.png": "F",
    "search.png": "S"
}

def create_icon(name, text, size=(24, 24), color=(50, 50, 50)):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw simple shape? No, just text centered
    # In real app, these would be proper icons
    draw.rectangle([0,0,size[0]-1, size[1]-1], outline=color, width=2)
    draw.text((size[0]//2 - 4, size[1]//2 - 6), text, fill=color)
    
    img.save(os.path.join(ICON_DIR, name))
    print(f"Created {name}")

if __name__ == "__main__":
    for name, text in ICONS.items():
        create_icon(name, text)