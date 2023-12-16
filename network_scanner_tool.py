import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import socket
import queue
from datetime import datetime
import sys

# Let's hide a tkinter error I couldn't solve.

#sys.stderr = open('NUL', 'w')

# Define results as a global variable
results = queue.Queue()
# Define results and a lock as global variables
results_lock = threading.Lock()

def scan_ports(target, start_port, end_port, loading_var, status_label, progress_text):
    try:
        for port in range(start_port, end_port + 1):
            if loading_var.get():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)  # Set a timeout of 1 second
                try:
                    result = sock.connect_ex((target, port))
                    if result == 0:
                        service_name = socket.getservbyport(port)
                        with results_lock:
                            results.put((port, service_name))
                        update_ui(progress_text, f"Port {port} open - Service: {service_name}\n")
                    else:
                        update_ui(progress_text, f"Port {port} closed\n")
                except socket.error:
                    update_ui(progress_text, f"Port {port} error\n")
                finally:
                    sock.close()
            else:
                break  # Stop scanning if the "Stop Scan" button is pressed

        loading_var.set(False)
        status_label.config(text="Scan Complete", foreground="green")
    except Exception as e:
        pass

def update_ui(widget, message):
    widget.config(state=tk.NORMAL)
    widget.insert(tk.END, message)
    widget.config(state=tk.DISABLED)
    widget.yview(tk.END)  # Scroll to the end

def worker_thread(target, port_ranges, loading_var, status_label, progress_text):
    while True:
        start_port, end_port = port_ranges.get()
        if start_port is None or not loading_var.get():
            break
        scan_ports(target, start_port, end_port, loading_var, status_label, progress_text)

def start_threads(target, num_threads, loading_var, status_label, progress_text):
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
        thread = threading.Thread(target=worker_thread, args=(target, port_ranges, loading_var, status_label, progress_text))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

def start_scan():
    target = target_entry.get()
    num_threads = 4

    loading_var = tk.BooleanVar()
    loading_var.set(True)

    loading_popup = tk.Toplevel(app)
    loading_popup.title("Scanning")

    status_label = ttk.Label(loading_popup, text="Scanning in progress...", foreground="blue")
    status_label.pack(padx=20, pady=20)

    progress_text = scrolledtext.ScrolledText(loading_popup, width=50, height=8)
    progress_text.pack(pady=10)

    scan_thread = threading.Thread(target=start_threads, args=(target, num_threads, loading_var, status_label, progress_text))
    scan_thread.start()

    stop_button = tk.Button(loading_popup, text="Stop Scan", command=lambda: loading_var.set(False))
    stop_button.pack(pady=10)

    app.after(100, check_loading, loading_popup, loading_var, status_label, progress_text)

def check_loading(loading_popup, loading_var, status_label, progress_text):
    if loading_var.get():
        app.after(100, check_loading, loading_popup, loading_var, status_label, progress_text)
    else:
        loading_popup.destroy()
        update_status_label(status_label, "Scan Complete", "green")
        app.after(100, lambda: display_results(progress_text, list(results.queue)))

def update_status_label(label, text, foreground):
    try:
        label.config(text=text, foreground=foreground)
    except tk.TclError:
        pass

def display_results(progress_text, results_list):
    results_list.sort()

    # Update result_text in the main window
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    for port, service_name in results_list:
        result_text.insert(tk.END, f"Port {port} open - Service: {service_name}\n")
    result_text.config(state=tk.DISABLED)

def generate_html_report(results):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"scan_results_{timestamp}.html"

    with open(filename, "w") as file:
        file.write("<html><head><title>Scan Results</title>")
        file.write("<style>")
        file.write("body { font-family: Arial, sans-serif; background-color: #f4f4f4; }")
        file.write("h1 { color: #333; }")
        file.write("table { width: 80%; border-collapse: collapse; margin-top: 20px; }")
        file.write("th, td { padding: 10px; text-align: center; border: 1px solid #ddd; }")
        file.write("th { background-color: #4CAF50; color: white; }")
        file.write("tr:nth-child(even) { background-color: #f2f2f2; }")
        file.write("</style>")
        file.write("</head><body>")
        file.write("<h1>Network Scan Results</h1>")
        file.write("<table border='1'><tr><th>Port</th><th>Service</th></tr>")

        for port, service in results:
            file.write(f"<tr><td>{port}</td><td>{service}</td></tr>")

        file.write("</table></body></html>")

    return filename

def download_results():
    with results_lock:
        open_ports = list(results.queue)

    open_ports.sort()
    filename = generate_html_report(open_ports)
    messagebox.showinfo("Download Complete", f"Scan results saved to {filename}")

app = tk.Tk()
app.title("Network Scanner Tool")

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

# Download Button
download_button = tk.Button(app, text="Download Results", command=download_results)
download_button.pack(pady=10)

app.mainloop()