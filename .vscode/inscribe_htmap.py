import re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --- Parameters ---
BG = (198, 158, 109)  # Sandstone base color
FONT_PATH = "./fonts/NotoSansEgyptianHieroglyphs-Regular.ttf"
SIZE = 240            # Glyph height approx
PADDING = 60          # Space around glyphs

# --- Functions ---

def parse_glyph_input(raw_input: str) -> list[str]:
    """Parse user input: supports pasted glyphs or Unicode hex codes."""
    glyphs = []
    for part in raw_input.strip().split():
        if re.fullmatch(r"[0-9A-Fa-f]{4,6}", part):  # Hex input
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
    """Ensure filename is safe, properly formatted, and within length limits."""
    if not name or len(name) > 100:
        return False, "Filename must be between 1 and 100 characters."
    if not re.fullmatch(r"^[\w\- ]+$", name):
        return False, "Only letters, numbers, underscores, dashes, and spaces allowed."
    return True, ""

def generate_height_map(glyphs, font, size, padding, direction):
    """Generate a grayscale height map for engraving depth."""
    font = ImageFont.truetype(font, size)

    W = (size * len(glyphs) + padding * (len(glyphs) + 1), size + 2 * padding) if direction == "horizontal" else \
        (size + 2 * padding, size * len(glyphs) + padding * (len(glyphs) + 1))

    height_map = Image.new("L", (W[0], W[1]), 128)  # Mid-gray base (neutral depth)
    draw = ImageDraw.Draw(height_map)

    x, y = padding, padding
    for glyph in glyphs:
        bbox = font.getbbox(glyph)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pos_x = x if direction == "horizontal" else (W[0] - w) // 2 - bbox[0]
        pos_y = ((H - h) // 2 - bbox[1]) if direction == "horizontal" else y
        draw.text((pos_x, pos_y), glyph, fill=0, font=font)    # Outermost carved section in black
        draw.text((pos_x+3, pos_y+3), glyph, fill=64)  # Mid-depth carved section in dark gray

        draw.text((pos_x, pos_y), glyph, fill=255, font=font)  # Deepest carved section in white
        y += h + padding if direction == "vertical" else 0
        x += w + padding if direction == "horizontal" else 0

    return height_map.filter(ImageFilter.GaussianBlur(radius=3))  # Soften edges for realism

def apply_depth_shading(texture, height_map):
    """Apply depth shading by matching image and height map sizes."""
    W, H = texture.size
    height_map = height_map.resize((W, H), Image.Resampling.LANCZOS)  # Resize to match sandstone image

    height_pixels = np.array(height_map, dtype=np.float32) / 255.0  # Normalize to 0-1 range
    
    # Compute depth-based shadows using Sobel-like gradients
    sobel_x = np.diff(height_pixels, axis=1, prepend=0)
    sobel_y = np.diff(height_pixels, axis=0, prepend=0)
    
    # Create intensity map for depth-based lighting
    light_intensity = np.clip(1 - (sobel_x * 0.5 + sobel_y * 0.5), 0.6, 1.0)

    # Ensure intensity matrix matches RGB image shape
    light_intensity = np.expand_dims(light_intensity, axis=-1)  # Make it (H, W, 1)
    
    texture_pixels = np.array(texture, dtype=np.float32)
    shaded_texture = (texture_pixels * light_intensity).astype(np.uint8)

    return Image.fromarray(shaded_texture, mode="RGB")

def generate_carved_sandstone(size, base_color=(198, 158, 109), grain_intensity=15, tool_mark_freq=40):
    """Create base sandstone texture with subtle grain & imperfections."""
    W, H = size
    r, g, b = base_color

    noise = np.random.randint(0, grain_intensity, (H, W), dtype=np.uint8).astype(np.int16)
    y_gradient = np.linspace(-grain_intensity//2, grain_intensity//2, H).astype(np.int16)
    noise += y_gradient[:, None]  # Adds vertical variation

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

# --- Rendering Process ---
font = ImageFont.truetype(FONT_PATH, SIZE)
glyph_bboxes = [font.getbbox(g) for g in GLYPHS]
glyph_widths = [b[2] - b[0] for b in glyph_bboxes]
glyph_heights = [b[3] - b[1] for b in glyph_bboxes]

W = sum(glyph_widths) + PADDING * (len(GLYPHS) + 1) if DIRECTION == "horizontal" else max(glyph_widths) + PADDING * 2
H = max(glyph_heights) + PADDING * 2 if DIRECTION == "horizontal" else sum(glyph_heights) + PADDING * (len(GLYPHS) + 1)

height_map = generate_height_map(GLYPHS, FONT_PATH, SIZE, PADDING, DIRECTION)
img = generate_carved_sandstone((int(W), int(H)), BG)
img = apply_depth_shading(img, height_map)

# --- Save & Display ---
img.save(output_file)
print(f"Image saved as {output_file}")
img.show()