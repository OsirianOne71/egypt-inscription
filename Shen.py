import re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

# --- Parameters ---
BG = (198, 158, 109)  # sandstone base color
FONT_PATH = "./fonts/NotoSansEgyptianHieroglyphs-Regular.ttf"
SIZE = 240            # glyph height approx
PADDING = 60          # space around glyphs
EXTRA_PADDING = 30    # Additional padding for Shen ring
LINE_WIDTH = 10       # Thickness of the Shen ring

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

def create_shen_polygon(direction, W, H, line_width, extra_padding):
    # Calculate safe margins
    margin_x = PADDING + extra_padding
    margin_y = PADDING + extra_padding

    if direction == "horizontal":
        # The ring should fit within these bounds
        rect_x0 = margin_x
        rect_y0 = margin_y
        rect_x1 = W - margin_x
        rect_y1 = H - margin_y
        radius = min((rect_y1 - rect_y0) // 2, (rect_x1 - rect_x0) // 4)

        # Outer and inner rounded rectangles
        outer = box(rect_x0 + radius, rect_y0, rect_x1 - radius, rect_y1).buffer(radius, cap_style='round', join_style='round')
        inner = box(rect_x0 + radius + line_width, rect_y0 + line_width,
                    rect_x1 - radius - line_width, rect_y1 - line_width).buffer(radius - line_width, cap_style='round', join_style='round')

        shen_ring = outer.difference(inner)

        # Crossbar (vertical bar at the right end)
        bar_x0 = rect_x1 - line_width
        bar_y0 = rect_y0
        bar_x1 = rect_x1
        bar_y1 = rect_y1
        bar = box(bar_x0, bar_y0, bar_x1, bar_y1)

        merged = unary_union([shen_ring, bar])
        return merged

    elif direction == "vertical":
        rect_x0 = margin_x
        rect_y0 = margin_y
        rect_x1 = W - margin_x
        rect_y1 = H - margin_y
        radius = min((rect_x1 - rect_x0) // 2, (rect_y1 - rect_y0) // 4)

        outer = box(rect_x0, rect_y0 + radius, rect_x1, rect_y1 - radius).buffer(radius, cap_style='round', join_style='round')
        inner = box(rect_x0 + line_width, rect_y0 + radius + line_width,
                    rect_x1 - line_width, rect_y1 - radius - line_width).buffer(radius - line_width, cap_style='round', join_style='round')

        shen_ring = outer.difference(inner)

        # Crossbar (horizontal bar at the bottom)
        bar_x0 = rect_x0
        bar_y0 = rect_y1 - line_width
        bar_x1 = rect_x1
        bar_y1 = rect_y1
        bar = box(bar_x0, bar_y0, bar_x1, bar_y1)

        merged = unary_union([shen_ring, bar])
        return merged

    else:
        raise ValueError("direction must be 'horizontal' or 'vertical'")

def draw_polygon_with_carved_effect(draw, polygon, shadow, highlight):
    if polygon.is_empty:
        return
    # Draw shadow
    shadow_coords = [(x-2, y-2) for x, y in polygon.exterior.coords]
    draw.polygon(shadow_coords, fill=shadow)
    # Draw highlight
    highlight_coords = [(x+2, y+2) for x, y in polygon.exterior.coords]
    draw.polygon(highlight_coords, fill=highlight)
    # Draw main
    draw.polygon(list(polygon.exterior.coords), fill=None, outline=shadow)

# --- User Input ---
direction_input = input("How would you like the output for the inscription? (V/H): ").strip().upper()
if direction_input not in ("V", "H"):
    raise ValueError("Please enter 'V' for vertical or 'H' for horizontal.")
DIRECTION = "vertical" if direction_input == "V" else "horizontal"

glyph_input = input("Which Glyphs would you like inscribed? (paste glyphs or Unicode hex): ")
GLYPHS = parse_glyph_input(glyph_input)

# Ask the user if they want to draw a cartouche (shen)
cartouche_input = input("Would you like a shen around the glyphs? (Y/N): ").strip().lower()
DRAW_CARTOUCHE = cartouche_input == "y"

# Ask the user for the filename
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
    W = sum(glyph_widths) + PADDING * (len(GLYPHS) + 1) + EXTRA_PADDING * 2
    H = max(glyph_heights) + PADDING * 2
elif DIRECTION == "vertical":
    W = max(glyph_widths) + PADDING * 2
    H = sum(glyph_heights) + PADDING * (len(GLYPHS) + 1) + EXTRA_PADDING * 2
else:
    raise ValueError("DIRECTION must be 'horizontal' or 'vertical'")

# --- Create and Draw ---
img = generate_carved_sandstone((int(W), int(H)), BG)
draw = ImageDraw.Draw(img)

shadow = (max(BG[0] - 30, 0), max(BG[1] - 30, 0), max(BG[2] - 30, 0))
highlight = (min(BG[0] + 20, 255), min(BG[1] + 20, 255), min(BG[2] + 20, 255))
carved_color = tuple(max(c - 15, 0) for c in BG)

# Draw glyphs with carved effect
if DIRECTION == "horizontal":
    x = PADDING + EXTRA_PADDING  # Start position with extra padding
    for i, glyph in enumerate(GLYPHS):
        bbox = glyph_bboxes[i]
        w = glyph_widths[i]
        h = glyph_heights[i]
        y = (H - h) // 2 - bbox[1]  # Center vertically

        # Draw shadow (2 px up-left)
        draw.text((x - 2, y - 2), glyph, fill=shadow, font=font)
        # Draw highlight (2 px down-right)
        draw.text((x + 2, y + 2), glyph, fill=highlight, font=font)
        # Draw main glyph
        draw.text((x, y), glyph, fill=BG, font=font)

        x += w + PADDING

elif DIRECTION == "vertical":
    y = PADDING + EXTRA_PADDING  # Start position with extra padding
    for i, glyph in enumerate(GLYPHS):
        bbox = glyph_bboxes[i]
        w = glyph_widths[i]
        h = glyph_heights[i]
        x = (W - w) // 2 - bbox[0]  # Center horizontally

        # Draw shadow (2 px up-left)
        draw.text((x - 2, y - 2 - bbox[1]), glyph, fill=shadow, font=font)
        # Draw highlight (2 px down-right)
        draw.text((x + 2, y + 2 - bbox[1]), glyph, fill=highlight, font=font)
        # Draw main glyph
        draw.text((x, y - bbox[1]), glyph, fill=BG, font=font)

        y += h + PADDING

# Draw cartouche (shen) if enabled
if DRAW_CARTOUCHE:
    shen_polygon = create_shen_polygon(DIRECTION, W, H, line_width=LINE_WIDTH, extra_padding=EXTRA_PADDING)
    draw_polygon_with_carved_effect(draw, shen_polygon, shadow, highlight)

# Save and display the image
img.save(output_file)  # Save the image with the user-provided name
print(f"Image saved as {output_file}")
img.show()  # Display the image

from shapely.geometry import Polygon

# Define two polygons
polygon1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
polygon2 = Polygon([(1, 1), (3, 1), (3, 3), (1, 3)])

# Compute the difference
result = polygon1.difference(polygon2)
print(result)

outer = Polygon([(0,0), (4,0), (4,4), (0,4)])
inner = Polygon([(1,1), (3,1), (3,3), (1,3)])

# Correct usage: call .difference() on the geometry object
hollow = outer.difference(inner)