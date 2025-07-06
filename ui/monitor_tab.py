from PySide2.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout,
                             QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QHBoxLayout)
from PySide2.QtCore import Qt, QTimer, QThread, Signal
from PySide2.QtGui import QColor, QBrush
import time
class ProcessTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(["PID", "进程名", "CPU(%)", "内存(MB)", 
                                        "IO速率", "连接数", "网络使用", "类型"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.current_filter = "全部"

    def update_data(self, processes):
        self.setRowCount(0)
        filtered_processes = processes
        if self.current_filter != "全部":
            filtered_processes = [p for p in processes 
                                 if self.monitor.classify_process(p['pid']) == self.current_filter]
        self.setRowCount(len(filtered_processes))

        for row, process in enumerate(filtered_processes):
            self.setItem(row, 0, QTableWidgetItem(str(process['pid'])))
            self.setItem(row, 1, QTableWidgetItem(process['name']))
            cpu_item = QTableWidgetItem(f"{process['cpu_percent']:.2f}")
            if process['cpu_percent'] > 70:
                cpu_item.setBackground(QBrush(QColor(255, 100, 100)))
            elif process['cpu_percent'] > 30:
                cpu_item.setBackground(QBrush(QColor(255, 200, 100)))
            self.setItem(row, 2, cpu_item)
            mem_item = QTableWidgetItem(f"{process['mem_percent']:.2f}")
            if process['mem_percent'] > 1000:
                mem_item.setBackground(QBrush(QColor(255, 100, 100)))
            self.setItem(row, 3, mem_item)
            self.setItem(row, 4, QTableWidgetItem(str(process['io_rate'])))
            self.setItem(row, 5, QTableWidgetItem(str(len(process['connections']))))
            self.setItem(row, 6, QTableWidgetItem(str(process['net_usage'])))
            process_type = self.monitor.classify_process(process['pid'])
            type_item = QTableWidgetItem(process_type)
            type_colors = {
                "CPU密集型": QColor(255, 100, 100),
                "IO密集型": QColor(100, 255, 100),
                "网络密集型": QColor(100, 100, 255),
                "内存密集型": QColor(255, 200, 100)
            }
            if process_type in type_colors:
                type_item.setBackground(QBrush(type_colors[process_type]))
            self.setItem(row, 7, type_item)

    def set_monitor(self, monitor):
        self.monitor = monitor

    def set_filter(self, filter_type):
        self.current_filter = filter_type


class ProcessMonitorObserver:
    def __init__(self, table_widget):
        self.table_widget = table_widget

    def update_processes(self, processes):
        self.table_widget.update_data(processes)


class MonitorTab(QWidget):
    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel("系统进程资源监控")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        filter_group = QGroupBox("筛选选项")
        filter_layout = QGridLayout(filter_group)
        type_label = QLabel("按类型筛选:")
        filter_layout.addWidget(type_label, 0, 0)
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全部", "CPU密集型", "IO密集型", "网络密集型", "内存密集型", "普通进程"])
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.type_filter, 0, 1)
        layout.addWidget(filter_group)

        self.status_label = QLabel(f"监控中，上次更新: {time.strftime('%H:%M:%S')}")
        layout.addWidget(self.status_label)

        self.process_table = ProcessTableWidget()
        layout.addWidget(self.process_table)
        self.process_table.set_monitor(self.monitor)

        observer = ProcessMonitorObserver(self.process_table)
        self.monitor.add_observer(observer)

        control_layout = QHBoxLayout()
        refresh_button = QPushButton("手动刷新")
        refresh_button.clicked.connect(self.refresh_data)
        control_layout.addWidget(refresh_button)
        layout.addLayout(control_layout)

        self.setLayout(layout)

    def apply_filters(self):
        type_filter = self.type_filter.currentText()
        self.process_table.set_filter(type_filter)
        self.process_table.update_data(list(self.monitor.processes.values()))

    def refresh_data(self):
        self.status_label.setText(f"手动刷新中...")
        self.process_table.update_data(list(self.monitor.processes.values()))
        self.status_label.setText(f"监控中，上次更新: {time.strftime('%H:%M:%S')}")