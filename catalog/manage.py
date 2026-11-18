#!/usr/bin/env python
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    sys.path.insert(0, str(ROOT_DIR / "validators"))
    sys.path.insert(0, str(ROOT_DIR / "governance"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "catalog_site.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
