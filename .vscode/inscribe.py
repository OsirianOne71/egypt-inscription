from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --- parameters ---
BG       = (198, 158, 109)  # sandstone base colour
FONT     = "./fonts/NotoSansEgyptianHieroglyphs-Regular.ttf"
SIZE     = 240              # glyph height approx
PADDING  = 60               # space around glyphs

# User input values
DIRECTION = "vertical"    # "vertical" or "horizontal"
GLYPHS = list("𓏙𓋹𓊽𓌀𓎃𓍑𓋴𓆖")
# User input values end

font = ImageFont.truetype(FONT, SIZE)

# Precompute glyph bounding boxes and widths/heights
glyph_bboxes = [font.getbbox(g) for g in GLYPHS]
glyph_widths = [bbox[2] - bbox[0] for bbox in glyph_bboxes]
glyph_heights = [bbox[3] - bbox[1] for bbox in glyph_bboxes]

if DIRECTION == "horizontal":
    W = sum(glyph_widths) + PADDING * (len(GLYPHS) + 1)
    H = max(glyph_heights) + PADDING * 2
elif DIRECTION == "vertical":
    W = max(glyph_widths) + PADDING * 2
    H = sum(glyph_heights) + PADDING * (len(GLYPHS) + 1)
else:
    raise ValueError("DIRECTION must be 'horizontal' or 'vertical'")

# Create sandstone background with noise
W = int(W)
H = int(H)
img = Image.new("RGB", (int(W), int(H)), BG)
for y in range(H):
    for x in range(W):
        v = int((hash((x, y)) & 0xFF)/255*25)
        
        pixel = img.getpixel((x, y))
        if isinstance(pixel, tuple) and len(pixel) >= 3:
            r, g, b = pixel[:3]
        else:
            raise ValueError(f"Unexpected pixel format: {pixel}")
        
        img.putpixel((x, y), (r + v, g + v, b + v))

draw = ImageDraw.Draw(img)

# Shadow and highlight colors
shadow = (max(BG[0]-30,0), max(BG[1]-30,0), max(BG[2]-30,0))
highlight = (min(BG[0]+20,255), min(BG[1]+20,255), min(BG[2]+20,255))

# Draw glyphs with carved effect
if DIRECTION == "horizontal":
    x = PADDING
    for i, glyph in enumerate(GLYPHS):
        bbox = glyph_bboxes[i]
        w = glyph_widths[i]
        h = glyph_heights[i]
        y = (H - h) // 2 - bbox[1]  # baseline position adjusted by top bearing

        # Draw shadow (2 px up-left)
        draw.text((x - 2, y - 2), glyph, fill=shadow, font=font)
        # Draw highlight (2 px down-right)
        draw.text((x + 2, y + 2), glyph, fill=highlight, font=font)
        # Draw main glyph
        draw.text((x, y), glyph, fill=BG, font=font)

        x += w + PADDING

elif DIRECTION == "vertical":
    y = PADDING
    for i, glyph in enumerate(GLYPHS):
        bbox = glyph_bboxes[i]
        w = glyph_widths[i]
        h = glyph_heights[i]
        x = (W - w) // 2 - bbox[0]  # horizontally center, adjusted by left bearing

        # Draw shadow (2 px up-left)
        draw.text((x - 2, y - 2 - bbox[1]), glyph, fill=shadow, font=font)
        # Draw highlight (2 px down-right)
        draw.text((x + 2, y + 2 - bbox[1]), glyph, fill=highlight, font=font)
        # Draw main glyph
        draw.text((x, y - bbox[1]), glyph, fill=BG, font=font)

        y += h + PADDING

# Slight blur to soften edges
img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
img.save("sandstone_blessing.png")
print("Image saved as sandstone_blessing.png")
img.show()  # Display the image