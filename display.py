import curses
import time

class ProcessMonitorDisplay:
    def __init__(self, process_monitor):
        self.process_monitor = process_monitor
        self.processes = []
        self.running = True
        # 注册为观察者
        process_monitor.add_observer(self)
        
    def update_processes(self, processes):
        """接收进程数据更新"""
        self.processes = processes
        
    def display_top_processes(self, stdscr):
        """使用curses显示前20个CPU密集型进程"""
        curses.curs_set(0)  # 隐藏光标
        stdscr.nodelay(1)   # 非阻塞模式

        # 初始化颜色
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)      # CPU密集型 - 红色
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # IO密集型 - 黄色
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)     # 网络密集型 - 蓝色
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # 内存密集型 - 洋红色

        while self.running:
            stdscr.clear()

            # 获取CPU使用率最高的20个进程
            top_processes = sorted(
                self.processes, 
                key=lambda p: p.get('cpu_percent', 0), 
                reverse=True
            )[:20]

            # 显示标题行
            header = "PID    进程名称                          CPU%    内存(MB)  进程类型           IO速率    网络连接"
            stdscr.addstr(0, 0, header, curses.A_BOLD)
            stdscr.addstr(1, 0, "-" * 80)

            # 显示每个进程的信息
            for i, process in enumerate(top_processes, start=2):
                pid = process['pid']
                name = process['name'][:25].ljust(25)
                cpu = f"{process['cpu_percent']:6.1f}"
                mem = f"{process['mem_percent']:8.1f}"
                ptype = self.process_monitor.classify_process(pid).ljust(15)
                io_rate = f"{process['io_rate']:8.0f}"
                conn = len(process['connections'])

                # 根据进程类型设置颜色
                if ptype.strip() == "CPU密集型":
                    stdscr.addstr(i, 0, f"{pid:5d}  {name} {cpu}  {mem}  {ptype} {io_rate}  {conn:5d}", curses.color_pair(1))
                elif ptype.strip() == "IO密集型":
                    stdscr.addstr(i, 0, f"{pid:5d}  {name} {cpu}  {mem}  {ptype} {io_rate}  {conn:5d}", curses.color_pair(2))
                elif ptype.strip() == "网络密集型":
                    stdscr.addstr(i, 0, f"{pid:5d}  {name} {cpu}  {mem}  {ptype} {io_rate}  {conn:5d}", curses.color_pair(3))
                elif ptype.strip() == "内存密集型":
                    stdscr.addstr(i, 0, f"{pid:5d}  {name} {cpu}  {mem}  {ptype} {io_rate}  {conn:5d}", curses.color_pair(4))
                else:
                    stdscr.addstr(i, 0, f"{pid:5d}  {name} {cpu}  {mem}  {ptype} {io_rate}  {conn:5d}")

            # 显示帮助信息
            help_text = "按 'q' 退出，按 'r' 刷新"
            stdscr.addstr(23, 0, help_text)

            # 刷新屏幕
            stdscr.refresh()

            # 处理用户输入
            key = stdscr.getch()
            if key == ord('q'):
                self.running = False
                self.process_monitor.stop_monitoring()
            elif key == ord('r'):
                self.process_monitor.update_processes()

            # 等待刷新间隔
            time.sleep(0.5)

    def run(self):
        """启动显示界面"""
        curses.wrapper(self.display_top_processes)    
        
if __name__ == "__main__":
    from monitor.process_monitor import ProcessMonitor
    
    # 创建监控器和显示器
    monitor = ProcessMonitor()
    display = ProcessMonitorDisplay(monitor)
    
    # 启动监控
    monitor.start_monitoring()
    
    # 运行显示界面
    display.run()    