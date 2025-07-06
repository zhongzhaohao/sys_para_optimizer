import os
import time
import threading
from collections import defaultdict, deque

class ProcessMonitor:
    def __init__(self):
        # 存储进程信息的字典，键为PID，值为进程信息字典
        self.processes = {}
        # 存储历史CPU使用率，用于判断CPU密集型进程
        self.cpu_history = defaultdict(lambda: deque(maxlen=10))
        # 存储历史IO使用率，用于判断IO密集型进程
        self.io_history = defaultdict(lambda: deque(maxlen=10))
        # 存储历史网络使用率，用于判断网络密集型进程
        self.net_history = defaultdict(lambda: deque(maxlen=10))
        # 上次全局网络统计
        self.last_net_stats = self.get_network_stats()
        # 锁，用于多线程保护共享数据
        self.lock = threading.Lock()
        # 监控是否运行的标志
        self.running = True
        # 观察者列表
        self.observers = []

    def add_observer(self, observer):
        """添加观察者"""
        self.observers.append(observer)

    def notify_observers(self):
        """通知所有观察者进程数据已更新"""
        with self.lock:
            processes = list(self.processes.values())
            for observer in self.observers:
                observer.update_processes(processes)

    def get_network_stats(self):
        """获取系统网络统计信息"""
        stats = {}
        try:
            with open('/proc/net/dev', 'r') as f:
                for line in f.readlines()[2:]:  # 跳过前两行标题
                    parts = line.strip().split()
                    if len(parts) < 10:
                        continue
                    interface = parts[0].rstrip(':')
                    stats[interface] = {
                        'rx_bytes': int(parts[1]),
                        'tx_bytes': int(parts[9])
                    }
        except Exception as e:
            print(f"Error reading network stats: {e}")
        return stats

    def get_process_list(self):
        """获取所有进程的PID列表"""
        pids = []
        for entry in os.scandir('/proc'):
            if entry.is_dir() and entry.name.isdigit():
                pids.append(int(entry.name))
        return pids

    def analyze_process(self, pid):
        """分析单个进程的资源使用情况"""
        try:
            # 读取基本进程信息
            with open(f'/proc/{pid}/stat', 'r') as f:
                stat = f.read().split()

            # 读取内存信息
            with open(f'/proc/{pid}/status', 'r') as f:
                status = f.read()

            # 读取IO信息（如果可用）
            io_counters = {'rchar': 0, 'wchar': 0}
            try:
                with open(f'/proc/{pid}/io', 'r') as f:
                    for line in f:
                        if line.startswith('rchar:'):
                            io_counters['rchar'] = int(line.split()[1])
                        elif line.startswith('wchar:'):
                            io_counters['wchar'] = int(line.split()[1])
            except:
                pass

            # 解析基本信息
            name = stat[1].strip('()')
            utime = int(stat[13])
            stime = int(stat[14])
            start_time = int(stat[21])
            rss = int(stat[23]) * os.sysconf('SC_PAGE_SIZE')

            # 计算CPU使用率
            cpu_time = utime + stime
            cpu_percent = 0.0

            # 获取进程打开的网络连接
            connections = []
            try:
                fd_dir = f'/proc/{pid}/fd'
                for fd in os.listdir(fd_dir):
                    try:
                        path = os.readlink(os.path.join(fd_dir, fd))
                        if path.startswith('socket:'):
                            connections.append(path)
                    except:
                        continue
            except:
                pass

            # 获取内存使用信息
            mem_percent = 0.0
            try:
                # 解析VmRSS行
                for line in status.split('\n'):
                    if line.startswith('VmRSS:'):
                        mem_percent = float(line.split()[1]) / 1024  # KB to MB
                        break
            except:
                pass

            # 计算IO速率（使用差值）
            io_rate = 0
            if pid in self.processes:
                prev_io = self.processes[pid].get('io_counters', {'rchar': 0, 'wchar': 0})
                io_rate = (io_counters['rchar'] - prev_io['rchar']) + (io_counters['wchar'] - prev_io['wchar'])

            # 计算网络使用（估算）
            net_usage = len(connections) * 10  # 简单估算，实际应用需要更复杂的逻辑

            # 更新进程信息
            process_info = {
                'pid': pid,
                'name': name,
                'cpu_time': cpu_time,
                'start_time': start_time,
                'rss': rss,
                'mem_percent': mem_percent,
                'io_counters': io_counters,
                'io_rate': io_rate,
                'connections': connections,
                'net_usage': net_usage,
                'cpu_percent': cpu_percent,
                'update_time': time.time()
            }

            return process_info
        except (FileNotFoundError, PermissionError):
            return None

    def update_processes(self):
        """更新所有进程信息"""
        current_time = time.time()
        pids = self.get_process_list()

        # 获取当前网络统计
        current_net_stats = self.get_network_stats()
        net_change = 0

        # 计算网络变化
        if self.last_net_stats:
            for interface, stats in current_net_stats.items():
                if interface in self.last_net_stats:
                    prev_stats = self.last_net_stats[interface]
                    net_change += (stats['rx_bytes'] - prev_stats['rx_bytes']) + (stats['tx_bytes'] - prev_stats['tx_bytes'])

        self.last_net_stats = current_net_stats

        # 临时存储新的进程信息
        new_processes = {}

        # 更新每个进程的信息
        for pid in pids:
            process_info = self.analyze_process(pid)
            if process_info:
                # 计算CPU使用率（需要两次采样的差值）
                if pid in self.processes:
                    prev_info = self.processes[pid]
                    prev_cpu_time = prev_info['cpu_time']
                    time_delta = current_time - prev_info['update_time']

                    if time_delta > 0:
                        # CPU时间差值（jiffies）
                        cpu_delta = process_info['cpu_time'] - prev_cpu_time
                        # 转换为百分比（假设单CPU系统，需要根据CPU核心数调整）
                        cpu_percent = (cpu_delta / os.sysconf('SC_CLK_TCK')) / time_delta * 100
                        process_info['cpu_percent'] = cpu_percent

                        # 更新历史数据
                        self.cpu_history[pid].append(cpu_percent)
                        self.io_history[pid].append(process_info['io_rate'])
                        self.net_history[pid].append(process_info['net_usage'])

                new_processes[pid] = process_info

        # 更新进程字典
        with self.lock:
            self.processes = new_processes

        # 通知观察者
        self.notify_observers()

    def classify_process(self, pid):
        """根据资源使用情况对进程进行分类"""
        if pid not in self.processes:
            return "Unknown"

        process = self.processes[pid]

        # 计算历史平均值
        cpu_avg = sum(self.cpu_history[pid]) / max(1, len(self.cpu_history[pid]))
        io_avg = sum(self.io_history[pid]) / max(1, len(self.io_history[pid]))
        net_avg = sum(self.net_history[pid]) / max(1, len(self.net_history[pid]))

        # 设置阈值（可根据实际情况调整）
        cpu_threshold = 20.0  # CPU使用率超过20%视为CPU密集型
        io_threshold = 10000  # IO速率超过10KB/s视为IO密集型
        net_threshold = 500   # 网络使用超过500视为网络密集型

        # 分类逻辑
        if cpu_avg > cpu_threshold:
            return "CPU密集型"
        elif io_avg > io_threshold:
            return "IO密集型"
        elif net_avg > net_threshold:
            return "网络密集型"
        elif process['mem_percent'] > 500:  # 内存使用超过500MB视为内存密集型
            return "内存密集型"
        else:
            return "普通进程"

    def monitor_loop(self, refresh_interval=1.0):
        """监控主循环"""
        while self.running:
            self.update_processes()
            time.sleep(refresh_interval)

    def start_monitoring(self, refresh_interval=1.0):
        """启动监控线程"""
        monitor_thread = threading.Thread(target=self.monitor_loop, args=(refresh_interval,), daemon=True)
        monitor_thread.start()
        return monitor_thread

    def stop_monitoring(self):
        """停止监控"""
        self.running = False