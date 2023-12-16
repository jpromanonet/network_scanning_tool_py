import socket
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext

def scan_ports(target, start_port, end_port, results, loading_var):
    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((target, port))
        if result == 0:
            service_name = socket.getservbyport(port)
            results.put((port, service_name))
        sock.close()
    loading_var.set(False)  # Set loading variable to False when scanning is complete

def worker_thread(target, port_range, results, loading_var):
    loading_var.set(True)  # Set loading variable to True when scanning starts
    while True:
        start_port, end_port = port_range.get()
        if start_port is None:
            break
        scan_ports(target, start_port, end_port, results, loading_var)

def start_threads(target, num_threads, results, loading_var):
    port_ranges = queue.Queue()
    total_ports = 65535

    ports_per_thread = total_ports // num_threads
    for i in range(num_threads):
        start_port = i * ports_per_thread + 1
        end_port = (i + 1) * ports_per_thread
        if i == num_threads - 1:
            end_port = total_ports
        port_ranges.put((start_port, end_port))

    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker_thread, args=(target, port_ranges, results, loading_var))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

def start_scan():
    target = target_entry.get()
    num_threads = 4

    loading_var = tk.BooleanVar()
    loading_var.set(False)

    loading_popup = tk.Toplevel(app)
    loading_popup.title("Scanning")

    loading_label = tk.Label(loading_popup, text="Scanning in progress...")
    loading_label.pack(padx=20, pady=20)

    results = queue.Queue()
    scan_thread = threading.Thread(target=start_threads, args=(target, num_threads, results, loading_var))
    scan_thread.start()

    app.after(100, check_loading, loading_popup, loading_var)

def check_loading(loading_popup, loading_var):
    if loading_var.get():
        app.after(100, check_loading, loading_popup, loading_var)
    else:
        loading_popup.destroy()

        open_ports = []
        while not results.empty():
            port, service_name = results.get()
            open_ports.append((port, service_name))

        open_ports.sort()
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        for port, service_name in open_ports:
            result_text.insert(tk.END, f"Port {port} open - Service: {service_name}\n")
        result_text.config(state=tk.DISABLED)

# GUI setup
app = tk.Tk()
app.title("Network Scanner")

# Target Entry
target_label = tk.Label(app, text="Enter the target IP or URL:")
target_label.pack(pady=5)
target_entry = tk.Entry(app)
target_entry.pack(pady=5)

# Scan Button
scan_button = tk.Button(app, text="Start Scan", command=start_scan)
scan_button.pack(pady=10)

# Result Text
result_text = scrolledtext.ScrolledText(app, width=50, height=15, state=tk.DISABLED)
result_text.pack(pady=10)

app.mainloop()