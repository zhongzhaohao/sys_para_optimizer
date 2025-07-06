from PySide2.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout,
                             QGroupBox, QPushButton, QListWidget, QListWidgetItem,
                             QProgressBar, QComboBox, QSlider, QSpinBox)
from PySide2.QtCore import Qt, QTimer, QThread, Signal
from PySide2.QtGui import QColor, QBrush
import os


class OptimizationTool(QWidget):
    optimization_finished = Signal(str)

    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("系统优化工具")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 优化类型选择布局块
        opt_type_layout = QHBoxLayout()
        opt_type_label = QLabel("选择优化类型:")
        self.opt_type_combo = QComboBox()
        opt_types = ["cpu密集型", "io密集型", "网络密集型", "数据密集型"]
        self.opt_type_combo.addItems(opt_types)
        optimize_button = QPushButton("一键优化")
        optimize_button.clicked.connect(self.one_click_optimize)
        opt_type_layout.addWidget(opt_type_label)
        opt_type_layout.addWidget(self.opt_type_combo)
        opt_type_layout.addWidget(optimize_button)
        main_layout.addLayout(opt_type_layout)

        # 自定义参数布局块
        custom_param_group = QGroupBox("自定义参数")
        # 设置对象名称，用于后续查找
        custom_param_group.setObjectName("自定义参数")
        custom_param_layout = QVBoxLayout(custom_param_group)
        self.param_widgets = []
        add_param_button = QPushButton("添加自定义参数")
        add_param_button.clicked.connect(self.add_custom_param)
        custom_param_layout.addWidget(add_param_button)

        # 自定义参数操作按钮
        custom_optimize_button = QPushButton("根据设定优化")
        custom_optimize_button.clicked.connect(self.custom_optimize)
        auto_optimize_button = QPushButton("自动优化")
        auto_optimize_button.clicked.connect(self.auto_optimize)
        button_layout = QHBoxLayout()
        button_layout.addWidget(custom_optimize_button)
        button_layout.addWidget(auto_optimize_button)
        custom_param_layout.addLayout(button_layout)
        main_layout.addWidget(custom_param_group)

        # 日志布局
        log_group = QGroupBox("优化日志")
        self.log_list = QListWidget()
        log_group.setLayout(QVBoxLayout())
        log_group.layout().addWidget(self.log_list)
        main_layout.addWidget(log_group)

        self.optimization_finished.connect(self.append_log)

    def add_custom_param(self):
        param_row = QHBoxLayout()
        param_combo = QComboBox()
        param_combo.addItems(["a", "b", "c"])
        param_combo.currentIndexChanged.connect(lambda: self.update_param_widget(param_row, param_combo))
        param_row.addWidget(param_combo)

        # 初始隐藏范围选择和下拉选择
        self.range_widget = QWidget()
        range_layout = QHBoxLayout(self.range_widget)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(10, 20)
        self.spinbox = QSpinBox()
        self.spinbox.setRange(10, 20)
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)
        range_layout.addWidget(self.slider)
        range_layout.addWidget(self.spinbox)
        self.range_widget.hide()

        self.select_widget = QComboBox()
        self.select_widget.addItems(["很高", "高", "中", "低", "很低"])
        self.select_widget.hide()

        param_row.addWidget(self.range_widget)
        param_row.addWidget(self.select_widget)

        remove_button = QPushButton("移除")
        remove_button.clicked.connect(lambda: self.remove_param_row(param_row))
        param_row.addWidget(remove_button)

        self.param_widgets.append(param_row)
        # 查找设置了对象名称的QGroupBox
        layout = self.findChild(QGroupBox, "自定义参数").layout()
        layout.insertLayout(layout.count() - 1, param_row)

    def update_param_widget(self, row, combo):
        param_type = combo.currentText()
        range_widget = row.itemAt(1).widget()
        select_widget = row.itemAt(2).widget()
        if param_type in ["a", "b"]:
            range_widget.show()
            select_widget.hide()
        elif param_type == "c":
            range_widget.hide()
            select_widget.show()

    def remove_param_row(self, row):
        for i in reversed(range(row.count())):
            item = row.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            row.removeItem(item)
        if row in self.param_widgets:
            self.param_widgets.remove(row)

    def one_click_optimize(self):
        opt_type = self.opt_type_combo.currentText()
        # 这里替换为实际的python命令
        command = f"python tmp_python_order.py {opt_type}"
        self.append_log(f"执行命令: {command}")
        try:
            os.system(command)
            self.optimization_finished.emit(f"优化完成: 一键优化 {opt_type}")
        except Exception as e:
            self.append_log(f"一键优化失败: {str(e)}")

    def custom_optimize(self):
        params = []
        selected_params = []
        for row in self.param_widgets:
            param_combo = row.itemAt(0).widget()
            param_type = param_combo.currentText()
            if param_type in selected_params:
                self.append_log(f"错误: 重复选择参数 {param_type}")
                return
            selected_params.append(param_type)
            if param_type in ["a", "b"]:
                value = row.itemAt(1).widget().layout().itemAt(1).widget().value()
                params.append(f"{param_type}={value}")
            elif param_type == "c":
                value = row.itemAt(2).widget().currentText()
                params.append(f"{param_type}={value}")
        # 这里替换为实际的python命令
        command = f"python tmp_python_order.py {' '.join(params)}"
        self.append_log(f"执行命令: {command}")
        try:
            os.system(command)
            self.optimization_finished.emit(f"优化完成: 根据设定优化 {', '.join(params)}")
        except Exception as e:
            self.append_log(f"根据设定优化失败: {str(e)}")

    def auto_optimize(self):
        # 这里替换为实际的python命令
        command = "python tmp_python_order.py"
        self.append_log(f"执行命令: {command}")
        try:
            os.system(command)
            self.optimization_finished.emit("优化完成: 自动优化")
        except Exception as e:
            self.append_log(f"自动优化失败: {str(e)}")

    def append_log(self, message):
        self.log_list.addItem(QListWidgetItem(message))
        self.log_list.scrollToBottom()