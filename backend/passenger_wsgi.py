"""اتصال Passenger در cPanel — فقط همین فایل را به‌عنوان Startup File معرفی کنید."""
import os
import sys

# مسیر backend را به sys.path اضافه می‌کند تا «config» پیدا شود
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.wsgi import application  # noqa: E402
