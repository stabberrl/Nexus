"""Generate proper icon files for Nexus AI Tauri desktop app."""

from PIL import Image, ImageDraw, ImageFont
import struct
import io


def create_nexus_icon(size: int) -> Image.Image:
    """Create a Nexus AI icon: a gradient circle with 'N' letter."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw filled circle
    margin = max(2, size // 8)
    bbox = [margin, margin, size - margin - 1, size - margin - 1]
    draw.ellipse(bbox, fill=(59, 130, 246, 255))  # Blue-500

    # Draw "N" letter
    try:
        # Try to use a bold font
        font_size = size // 2
        try:
            font = ImageFont.truetype("segoeui.ttf", font_size)
        except (IOError, OSError):
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Center the text
    text = "N"
    bbox_text = draw.textbbox((0, 0), text, font=font)
    tw = bbox_text[2] - bbox_text[0]
    th = bbox_text[3] - bbox_text[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2 - 1
    draw.text((tx, ty), text, fill=(255, 255, 255, 255), font=font)

    return img


def create_ico(img_32: Image.Image, filepath: str):
    """Create a valid .ico file from a 32x32 RGBA image."""
    # Encode as PNG (modern ICO format uses PNG data)
    png_data = io.BytesIO()
    img_32.save(png_data, format="PNG")
    png_bytes = png_data.getvalue()

    with open(filepath, "wb") as f:
        # ICO header
        f.write(struct.pack("<HHH", 0, 1, 1))  # reserved=0, type=1 (icon), count=1
        # Directory entry
        f.write(struct.pack("<BBBBHHII",
                            32,     # width
                            32,     # height
                            0,      # color palette
                            0,      # reserved
                            1,      # color planes
                            32,     # bits per pixel
                            len(png_bytes),  # size
                            22,     # offset (6 header + 16 entry)
                            ))
        # PNG data
        f.write(png_bytes)


def create_icns(img_128: Image.Image, filepath: str):
    """Create a minimal valid .icns file for macOS."""
    # Encode the 128x128 PNG as ic07 entry
    png_data = io.BytesIO()
    img_128.save(png_data, format="PNG")
    png_bytes = png_data.getvalue()

    entry_type = b"ic07"  # 128x128 PNG
    entry_size = 8 + len(png_bytes)
    total_size = 8 + entry_size

    with open(filepath, "wb") as f:
        f.write(b"icns")
        f.write(struct.pack(">I", total_size))
        f.write(entry_type)
        f.write(struct.pack(">I", entry_size))
        f.write(png_bytes)


def main():
    icons_dir = "apps/nexus-desktop/src-tauri/icons"

    # Generate icon sizes
    img_32 = create_nexus_icon(32)
    img_128 = create_nexus_icon(128)
    img_256 = create_nexus_icon(256)

    # Save PNGs
    img_32.save(f"{icons_dir}/32x32.png", format="PNG")
    img_128.save(f"{icons_dir}/128x128.png", format="PNG")
    img_256.save(f"{icons_dir}/128x128@2x.png", format="PNG")
    img_256.save(f"{icons_dir}/icon.png", format="PNG")

    # Create .ico from 32x32
    create_ico(img_32, f"{icons_dir}/icon.ico")

    # Create .icns from 128x128 (macOS - optional but good to have)
    create_icns(img_128, f"{icons_dir}/icon.icns")

    # Verify sizes
    import os
    for name in ["32x32.png", "128x128.png", "128x128@2x.png",
                  "icon.png", "icon.ico", "icon.icns"]:
        path = f"{icons_dir}/{name}"
        size = os.path.getsize(path)
        print(f"{name}: {size} bytes")

    print("All icons generated successfully!")


if __name__ == "__main__":
    main()
