#!/usr/bin/env python3
import sys
from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout)
from PySide2.QtCore import QTimer
from monitor.process_monitor import ProcessMonitor
from ui.monitor_tab import MonitorTab
from ui.optimizer_tab import OptimizationTool

class ProcessMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统进程监控与优化工具")
        self.setMinimumSize(900, 700)

        self.monitor = ProcessMonitor()
        self.init_ui()

        self.monitor_thread = self.monitor.start_monitoring(refresh_interval=2.0)
        self.optimization_timer = QTimer()
        self.optimization_timer.timeout.connect(self.update_optimization_status)
        self.optimization_timer.start(2000)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.tab_widget = QTabWidget()
        monitor_tab = MonitorTab(self.monitor)
        optimization_tab = OptimizationTool(self.monitor)
        self.tab_widget.addTab(monitor_tab, "进程监控")
        self.tab_widget.addTab(optimization_tab, "系统优化")

        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.tab_widget)

    def update_optimization_status(self):
        if hasattr(self.tab_widget.widget(1), 'update_system_status'):
            self.tab_widget.widget(1).update_system_status()

    def exit_app(self):
        self.monitor.stop_monitoring()
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
        QApplication.quit()

    def closeEvent(self, event):
        self.monitor.stop_monitoring()
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProcessMonitorApp()
    window.show()
    sys.exit(app.exec_())