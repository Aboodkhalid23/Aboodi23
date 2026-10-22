"""يرسم أيقونة التطبيق (192×192) والبانر مال التلفزيون (320×180)."""
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

def card(w, h, radius):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    grad = Image.new("RGBA", (w, h))
    px = grad.load()
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2
            px[x, y] = (int(20 + 30 * t), int(24 + 10 * t), int(40 + 60 * (1 - t)), 255)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=255)
    img.paste(grad, (0, 0), mask)
    return img

def centered(draw, w, h, text, size, dy=0):
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = draw.textbbox((0, 0), text, font=f)
    draw.text(((w - (r - l)) / 2 - l, (h - (b - t)) / 2 - t + dy), text, font=f, fill=(245, 245, 247))

icon = card(192, 192, 42)
centered(ImageDraw.Draw(icon), 192, 192, "TV", 84)
icon.save("res/mipmap-xhdpi/ic_launcher.png")

banner = card(320, 180, 24)
centered(ImageDraw.Draw(banner), 320, 180, "Abood TV", 52)
banner.save("res/drawable-xhdpi/banner.png")
