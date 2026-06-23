import os

from PIL import Image, ImageDraw, ImageFont

output_path = "codere_icon.ico"
size = 256
img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

# Codere Green: #7DB828
codere_green = (125, 184, 40, 255)

# Draw circle
margin = 16
draw.ellipse([margin, margin, size - margin, size - margin], fill=codere_green)

# Draw a white "C" in the middle
try:
    font = ImageFont.truetype("arialbd.ttf", 150)
except:
    font = ImageFont.load_default()

text = "C"
# Center text
bbox = draw.textbbox((0, 0), text, font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((size - w) / 2, (size - h) / 2 - 20), text, fill="white", font=font)

icon_sizes = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
img.save(output_path, format="ICO", sizes=icon_sizes)
print(f"Codere Icon generated successfully at {os.path.abspath(output_path)}")
