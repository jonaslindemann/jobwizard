#!/usr/bin/env python3
"""Entry point for the SLURM Job Wizard."""

import sys
from qtpy.QtWidgets import QApplication
from jobwizard.app import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SLURM Job Wizard")
    app.setOrganizationName("jobwizard")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
