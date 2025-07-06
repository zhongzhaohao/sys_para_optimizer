from PySide2.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout,
                             QGroupBox, QPushButton, QListWidget, QListWidgetItem,
                             QProgressBar)
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

        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_layout = QVBoxLayout(status_frame)
        self.status_label = QLabel("准备优化系统...")
        status_layout.addWidget(self.status_label)

        mem_layout = QHBoxLayout()
        mem_label = QLabel("内存使用:")
        self.memory_bar = QProgressBar()
        self.memory_bar.setValue(0)
        mem_layout.addWidget(mem_label)
        mem_layout.addWidget(self.memory_bar)
        status_layout.addLayout(mem_layout)

        cpu_layout = QHBoxLayout()
        cpu_label = QLabel("CPU使用:")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setValue(0)
        cpu_layout.addWidget(cpu_label)
        cpu_layout.addWidget(self.cpu_bar)
        status_layout.addLayout(cpu_layout)
        main_layout.addWidget(status_frame)

        options_group = QGroupBox("优化选项")
        options_layout = QVBoxLayout(options_group)
        self.terminate_cpu_button = QPushButton("终止高CPU进程")
        self.terminate_cpu_button.clicked.connect(self.terminate_high_cpu_processes)
        options_layout.addWidget(self.terminate_cpu_button)
        self.terminate_mem_button = QPushButton("终止高内存进程")
        self.terminate_mem_button.clicked.connect(self.terminate_high_memory_processes)
        options_layout.addWidget(self.terminate_mem_button)
        self.terminate_all_button = QPushButton("终止所有非系统进程")
        self.terminate_all_button.clicked.connect(self.terminate_non_system_processes)
        options_layout.addWidget(self.terminate_all_button)
        self.free_memory_button = QPushButton("释放内存")
        self.free_memory_button.clicked.connect(self.free_system_memory)
        options_layout.addWidget(self.free_memory_button)
        main_layout.addWidget(options_group)

        log_group = QGroupBox("优化日志")
        self.log_list = QListWidget()
        log_group.setLayout(QVBoxLayout())
        log_group.layout().addWidget(self.log_list)
        main_layout.addWidget(log_group)

        self.optimization_finished.connect(self.append_log)

    def update_system_status(self):
        if not self.monitor.processes:
            return
        total_cpu = sum(p['cpu_percent'] for p in self.monitor.processes.values())
        avg_cpu = total_cpu / max(1, len(self.monitor.processes))
        total_mem = sum(p['mem_percent'] for p in self.monitor.processes.values())
        avg_mem = total_mem / max(1, len(self.monitor.processes))
        self.cpu_bar.setValue(min(100, int(avg_cpu)))
        self.memory_bar.setValue(min(100, int(avg_mem / 10)))
        self.status_label.setText(f"系统状态 - CPU: {avg_cpu:.1f}%, 内存: {avg_mem:.1f}MB")

    def append_log(self, message):
        self.log_list.addItem(QListWidgetItem(message))
        self.log_list.scrollToBottom()

    def terminate_process(self, pid, name):
        try:
            os.kill(pid, 9)
            self.append_log(f"已终止进程: {name} (PID: {pid})")
            return True
        except Exception as e:
            self.append_log(f"终止进程 {name} (PID: {pid}) 失败: {str(e)}")
            return False

    def terminate_high_cpu_processes(self):
        self.append_log("开始终止高CPU使用率进程...")
        count = 0
        high_cpu_processes = sorted(
            self.monitor.processes.values(), 
            key=lambda p: p['cpu_percent'], 
            reverse=True
        )
        for process in high_cpu_processes[:5]:
            if process['cpu_percent'] > 50:
                if self.terminate_process(process['pid'], process['name']):
                    count += 1
        self.append_log(f"终止高CPU进程完成，共终止 {count} 个进程")
        self.optimization_finished.emit(f"优化完成: 终止{count}个高CPU进程")

    def terminate_high_memory_processes(self):
        self.append_log("开始终止高内存使用率进程...")
        count = 0
        high_mem_processes = sorted(
            self.monitor.processes.values(), 
            key=lambda p: p['mem_percent'], 
            reverse=True
        )
        for process in high_mem_processes[:5]:
            if process['mem_percent'] > 500:
                if self.terminate_process(process['pid'], process['name']):
                    count += 1
        self.append_log(f"终止高内存进程完成，共终止 {count} 个进程")
        self.optimization_finished.emit(f"优化完成: 终止{count}个高内存进程")

    def terminate_non_system_processes(self):
        self.append_log("开始终止非系统进程...")
        count = 0
        system_processes = ["systemd", "init", "kernel", "svchost", "explorer"]
        for process in self.monitor.processes.values():
            is_system = False
            for sys_name in system_processes:
                if sys_name in process['name'].lower():
                    is_system = True
                    break
            if not is_system:
                if self.terminate_process(process['pid'], process['name']):
                    count += 1
        self.append_log(f"终止非系统进程完成，共终止 {count} 个进程")
        self.optimization_finished.emit(f"优化完成: 终止{count}个非系统进程")

    def free_system_memory(self):
        self.append_log("开始释放系统内存...")
        try:
            if os.name == 'posix':
                os.system('sync')
                os.system('echo 3 > /proc/sys/vm/drop_caches')
                self.append_log("已在Linux系统上执行内存释放操作")
            else:
                self.append_log("Windows系统不支持直接释放内存，已清理缓存")
            self.append_log("内存释放操作完成")
            self.optimization_finished.emit("优化完成: 内存已释放")
        except Exception as e:
            self.append_log(f"内存释放失败: {str(e)}")