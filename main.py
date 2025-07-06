import sys
from PySide2.QtWidgets import QApplication
from ui.main_window import ProcessMonitorApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProcessMonitorApp()
    window.show()
    sys.exit(app.exec_())