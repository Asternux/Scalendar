"""Thin deployment entry point for Scalendar.

The application implementation remains in ``scalendar.main``. This file
exists so Qt for Python's ``pyside6-deploy`` can use a conventional script
entry point without duplicating business or UI logic.
"""

from scalendar.main import main


if __name__ == "__main__":
    raise SystemExit(main())
