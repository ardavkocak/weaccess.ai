#!/usr/bin/env python
"""Django yönetim komutları için giriş noktası."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django import edilemedi. Sanal ortamınızın aktif olduğundan ve "
            "requirements.txt dosyasının kurulu olduğundan emin olun."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
