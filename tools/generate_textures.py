from PIL import Image, ImageDraw, ImageFont
import os
os.makedirs('assets/textures', exist_ok=True)

# simple procedural textures (32x32)
size = (64,64)

def save_colored(name, color, pattern=False):
    img = Image.new('RGBA', size, color)
    if pattern:
        draw = ImageDraw.Draw(img)
        for y in range(0,size[1],4):
            draw.line((0,y,size[0],y), fill=(0,0,0,30))
    img.save(os.path.join('assets','textures', name))

save_colored('dirt.png', (121,85,58,255), pattern=True)
save_colored('grass.png', (95,159,60,255), pattern=True)
save_colored('stone.png', (120,120,120,255), pattern=True)
save_colored('wood.png', (150,100,50,255), pattern=True)

# mob icon
img = Image.new('RGBA', size, (0,0,0,0))
d = ImageDraw.Draw(img)
d.ellipse((12,8,52,48), fill=(200,50,50,255))
img.save(os.path.join('assets','textures','mob.png'))

# hotbar slot background
slot = Image.new('RGBA', (64,64), (40,40,40,200))
d = ImageDraw.Draw(slot)
d.rectangle((4,4,60,60), outline=(200,200,200,60))
slot.save(os.path.join('assets','textures','hotbar_slot.png'))

print('Textures generated in assets/textures')
