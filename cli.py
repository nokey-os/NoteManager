#!/usr/bin/env python3
"""Скрипт для запуска CLI NoteMaster."""

import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
