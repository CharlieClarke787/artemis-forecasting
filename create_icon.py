from PIL import Image, ImageDraw

def create_cat_icon():
    '''Create cat logo as .ico file for desktop shortcut'''
    
    # Create image
    size = 256
    img = Image.new('RGB', (size, size), color='#f9f8f6')
    draw = ImageDraw.Draw(img)
    
    # Draw cat (simplified for icon)
    # Body
    draw.ellipse([60, 100, 196, 196], fill='#2d5016', outline='#2d5016')
    
    # Head
    draw.ellipse([80, 40, 176, 136], fill='#2d5016', outline='#2d5016')
    
    # Ears
    draw.polygon([(110, 30), (100, 0), (120, 20)], fill='#2d5016')
    draw.polygon([(146, 30), (156, 0), (136, 20)], fill='#2d5016')
    
    # Eyes
    draw.ellipse([110, 70, 125, 85], fill='#f9f8f6')
    draw.ellipse([131, 70, 146, 85], fill='#f9f8f6')
    
    # Pupils
    draw.ellipse([115, 75, 120, 80], fill='#6b4423')
    draw.ellipse([136, 75, 141, 80], fill='#6b4423')
    
    # Nose
    draw.polygon([(128, 95), (126, 105), (130, 105)], fill='#6b4423')
    
    # Save as ICO
    img.save('cat_icon.ico')
    print("Created cat_icon.ico")

if __name__ == '__main__':
    create_cat_icon()
