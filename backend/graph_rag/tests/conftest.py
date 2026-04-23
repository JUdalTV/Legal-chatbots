# -*- coding: utf-8 -*-
"""
conftest.py — cấu hình pytest cho thư mục graph_rag/tests
Tự động bật UTF-8 cho terminal Windows.
"""

import os
import sys


def pytest_configure(config):
    """Hook chạy trước khi pytest bắt đầu collect test."""
    # Bật UTF-8 mode trên Windows
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    # Đổi stdout/stderr sang UTF-8 nếu chưa phải
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
