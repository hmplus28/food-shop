#!/usr/bin/env python
"""مدیریت پروژه جنگوی فروشگاه خانم گل"""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'جنگو نصب نیست. برای نصب وابستگی‌ها: pip install -r requirements.txt'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
