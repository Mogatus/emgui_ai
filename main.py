"""Energie-Monitor – Entry point."""

import sys

from PyQt6.QtWidgets import QApplication

from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Energie-Monitor")
    app.setOrganizationName("emgui")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
