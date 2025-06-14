import re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --- Parameters ---
BG = (198, 158, 109)  # sandstone base color
FONT_PATH = "./fonts/NotoSansEgyptianHieroglyphs-Regular.ttf"
SIZE = 240            # glyph height approx
PADDING = 60          # space around glyphs

# --- Functions ---

def parse_glyph_input(raw_input: str) -> list[str]:
    glyphs = []
    for part in raw_input.strip().split():
        # Unicode hex entry
        if re.fullmatch(r"[0-9A-Fa-f]{4,6}", part):
            try:
                glyphs.append(chr(int(part, 16)))
            except ValueError:
                raise ValueError(f"Invalid Unicode hex: {part}")
        else:
            for char in part:
                code = ord(char)
                if 0x13000 <= code <= 0x1342F:
                    glyphs.append(char)
                else:
                    raise ValueError(f"Unexpected character '{char}' (U+{code:X})")
    return glyphs

def is_valid_filename(name: str) -> tuple[bool, str]:
    if not name or len(name) > 100:
        return False, "Filename must be between 1 and 100 characters."
    if not re.fullmatch(r"^[\w\- ]+$", name):
        return False, "Only letters, numbers, underscores, dashes, and spaces allowed."
    return True, ""

def generate_carved_sandstone(size, base_color=(198, 158, 109), grain_intensity=15, tool_mark_freq=40):
    W, H = size
    r, g, b = base_color

    noise = np.random.randint(0, grain_intensity, (H, W), dtype=np.uint8).astype(np.int16)
    y_gradient = np.linspace(-grain_intensity//2, grain_intensity//2, H).astype(np.int16)
    noise += y_gradient[:, None]  # adds vertical variation

    for x in range(0, W, tool_mark_freq):
        noise[:, x:x+1] -= grain_intensity // 4

    texture = np.stack([
        np.clip(noise + r, 0, 255),
        np.clip(noise + g, 0, 255),
        np.clip(noise + b, 0, 255)
    ], axis=-1).astype(np.uint8)

    return Image.fromarray(texture, mode="RGB").filter(ImageFilter.GaussianBlur(radius=0.7))

# --- User Input ---
direction_input = input("How would you like the output for the inscription? (V/H): ").strip().upper()
if direction_input not in ("V", "H"):
    raise ValueError("Please enter 'V' for vertical or 'H' for horizontal.")
DIRECTION = "vertical" if direction_input == "V" else "horizontal"

glyph_input = input("Which Glyphs would you like inscribed? (paste glyphs or Unicode hex separated by spaces): ")
GLYPHS = parse_glyph_input(glyph_input)

file_input = input("What name would you like the file saved as? (png only): ").strip()
file_base = file_input.lower().removesuffix(".png")
valid, msg = is_valid_filename(file_base)
if not valid:
    raise ValueError(f"Invalid file name: {msg}")
output_file = file_base + ".png"

# --- Rendering Calculations ---
font = ImageFont.truetype(FONT_PATH, SIZE)
glyph_bboxes = [font.getbbox(g) for g in GLYPHS]
glyph_widths = [b[2] - b[0] for b in glyph_bboxes]
glyph_heights = [b[3] - b[1] for b in glyph_bboxes]

if DIRECTION == "horizontal":
    W = sum(glyph_widths) + PADDING * (len(GLYPHS) + 1)
    H = max(glyph_heights) + PADDING * 2
else:
    W = max(glyph_widths) + PADDING * 2
    H = sum(glyph_heights) + PADDING * (len(GLYPHS) + 1)

# --- Create and Draw ---
img = generate_carved_sandstone((int(W), int(H)), BG)
draw = ImageDraw.Draw(img)

shadow = (max(BG[0] - 30, 0), max(BG[1] - 30, 0), max(BG[2] - 30, 0))
highlight = (min(BG[0] + 20, 255), min(BG[1] + 20, 255), min(BG[2] + 20, 255))
carved_color = tuple(max(c - 15, 0) for c in BG)

if DIRECTION == "horizontal":
    x = PADDING
    for i, glyph in enumerate(GLYPHS):
        bbox = glyph_bboxes[i]
        w = glyph_widths[i]
        h = glyph_heights[i]
        y = (H - h) // 2 - bbox[1]
        draw.text((x + 2, y + 2), glyph, fill=shadow, font=font)
        draw.text((x - 2, y - 2), glyph, fill=highlight, font=font)
        draw.text((x, y), glyph, fill=carved_color, font=font)
        x += w + PADDING
else:
    y = PADDING
for i, glyph in enumerate(GLYPHS):
    bbox = font.getbbox(glyph)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (W - w) // 2 - bbox[0]
    offset_y = y - bbox[1]  # shift to baseline based on top bearing

    draw.text((x - 2, offset_y - 2), glyph, fill=shadow, font=font) # shadow
    draw.text((x + 2, offset_y + 2), glyph, fill=highlight, font=font) # highlight
    draw.text((x, offset_y), glyph, fill=carved_color, font=font) # main glyph
    
    y += h + PADDING
    if i < len(GLYPHS) - 1:
        y += PADDING

img.save(output_file)
print(f"Image saved as {output_file}")
img.show()