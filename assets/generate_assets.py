"""
assets/generate_assets.py
--------------------------
Generate app icon and default background using Pillow.
Run once: python assets/generate_assets.py
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_icon():
    """Generate app icon - dark minimal style."""
    sizes = [16, 32, 48, 64, 128, 256]
    frames = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        pad = max(1, size // 12)
        r = max(2, size // 8)

        # Background rounded rect
        draw.rounded_rectangle(
            [pad, pad, size - pad, size - pad],
            radius=r,
            fill=(18, 18, 40, 255),
            outline=(80, 80, 180, 220),
            width=max(1, size // 32),
        )

        # Draw stylized "T" symbol
        cx = size // 2
        cy = size // 2
        bar_w = int(size * 0.55)
        bar_h = max(2, size // 10)
        stem_w = max(2, size // 10)
        stem_h = int(size * 0.38)

        # Horizontal bar of T
        draw.rectangle(
            [cx - bar_w // 2, cy - stem_h // 2 - bar_h // 2,
             cx + bar_w // 2, cy - stem_h // 2 + bar_h // 2],
            fill=(100, 100, 220, 255)
        )

        # Vertical stem of T
        draw.rectangle(
            [cx - stem_w // 2, cy - stem_h // 2,
             cx + stem_w // 2, cy + stem_h // 2],
            fill=(100, 100, 220, 255)
        )

        # Small accent dot bottom right
        dot_r = max(1, size // 14)
        dot_x = cx + bar_w // 2 - dot_r * 2
        dot_y = cy + stem_h // 2 - dot_r
        draw.ellipse(
            [dot_x - dot_r, dot_y - dot_r,
             dot_x + dot_r, dot_y + dot_r],
            fill=(160, 120, 255, 255)
        )

        frames.append(img)

    # Save as .ico with multiple sizes
    ico_path = os.path.join(ASSETS_DIR, "icon.ico")
    frames[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"[Assets] Icon saved: {ico_path}")

    # Also save PNG for runtime use
    png_path = os.path.join(ASSETS_DIR, "icon.png")
    frames[-1].save(png_path, format="PNG")
    print(f"[Assets] Icon PNG saved: {png_path}")

    return ico_path


def generate_background():
    """
    Generate a dark animated-style background for the main window.
    Dark deep space / circuit board aesthetic.
    """
    W, H = 540, 800
    img = Image.new("RGB", (W, H), (8, 8, 16))
    draw = ImageDraw.Draw(img)

    import random
    rng = random.Random(42)  # Fixed seed for reproducibility

    # ── Layer 1: Very subtle gradient ──────────────────────────
    for y in range(H):
        t = y / H
        # Dark blue-purple gradient
        r = int(8 + t * 4)
        g = int(8 + t * 3)
        b = int(16 + t * 12)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # ── Layer 2: Grid lines (circuit aesthetic) ─────────────────
    grid_color = (20, 20, 45)
    grid_spacing = 32

    for x in range(0, W, grid_spacing):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, grid_spacing):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # ── Layer 3: Glowing dots at grid intersections ─────────────
    for x in range(0, W, grid_spacing):
        for y in range(0, H, grid_spacing):
            if rng.random() < 0.12:
                intensity = rng.randint(30, 80)
                dot_color = (
                    intensity // 3,
                    intensity // 3,
                    intensity,
                )
                r = rng.randint(1, 2)
                draw.ellipse(
                    [x - r, y - r, x + r, y + r],
                    fill=dot_color
                )

    # ── Layer 4: Random circuit traces ─────────────────────────
    for _ in range(18):
        x = rng.randint(0, W)
        y = rng.randint(0, H)
        length = rng.randint(20, 100)
        direction = rng.choice(["h", "v"])
        alpha = rng.randint(15, 40)
        color = (alpha // 2, alpha // 2, alpha)

        if direction == "h":
            draw.line([(x, y), (x + length, y)], fill=color, width=1)
            # Branch
            if rng.random() < 0.5:
                branch_x = x + rng.randint(5, length)
                branch_len = rng.randint(10, 40)
                draw.line(
                    [(branch_x, y), (branch_x, y + branch_len)],
                    fill=color, width=1
                )
        else:
            draw.line([(x, y), (x, y + length)], fill=color, width=1)

    # ── Layer 5: Corner accent glow ────────────────────────────
    # Top-left subtle glow
    for radius in range(80, 0, -10):
        alpha = max(0, int((80 - radius) * 0.4))
        color = (alpha // 4, alpha // 4, alpha)
        draw.ellipse(
            [-radius, -radius, radius, radius],
            outline=color,
            width=1
        )

    # ── Layer 6: Subtle scanlines ───────────────────────────────
    scanline_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scanline_draw = ImageDraw.Draw(scanline_img)
    for y in range(0, H, 3):
        scanline_draw.line([(0, y), (W, y)], fill=(0, 0, 0, 15))

    img = img.convert("RGBA")
    img = Image.alpha_composite(img, scanline_img)
    img = img.convert("RGB")

    # ── Layer 7: Very subtle blur to soften ────────────────────
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    bg_path = os.path.join(ASSETS_DIR, "background.png")
    img.save(bg_path, format="PNG")
    print(f"[Assets] Background saved: {bg_path}")
    return bg_path


def generate_overlay_bg():
    """Generate a subtle texture for the translation overlay."""
    W, H = 400, 300
    img = Image.new("RGBA", (W, H), (15, 15, 30, 230))
    draw = ImageDraw.Draw(img)

    import random
    rng = random.Random(99)

    # Subtle noise
    for _ in range(2000):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        v = rng.randint(0, 8)
        draw.point([x, y], fill=(v, v, v + v // 2, 30))

    path = os.path.join(ASSETS_DIR, "overlay_bg.png")
    img.save(path, format="PNG")
    print(f"[Assets] Overlay bg saved: {path}")
    return path


if __name__ == "__main__":
    print("[Assets] Generating assets...")
    generate_icon()
    generate_background()
    generate_overlay_bg()
    print("[Assets] Done!")