"""
run.py — Top-level entry point for the School Management System.

Usage:
    python run.py          → launches the interactive CLI
    python run.py --seed   → seeds the database with demo data, then exits
    python run.py --help   → shows this help
"""

import sys
import os

# Allow running directly without installing the package
sys.path.insert(0, os.path.dirname(__file__))

from school_management.db.connection import MYSQL_AVAILABLE


def _show_help():
    print(__doc__)


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        _show_help()
        return

    if "--seed" in args:
        from school_management.seeder import main as seed_main
        seed_main()
        return

    from school_management.cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
