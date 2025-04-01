import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading

def run_pipeline():
    # Disable the button during execution to avoid duplicate runs
    run_button.config(state=tk.DISABLED)
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.END, "Starting pipeline...\n")

    # Define a worker function to run the pipeline in a background thread
    def task():
        try:
            process = subprocess.Popen(
                ["./scripts/run_all.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False
            )
            # Continuously read from the process output and update the text area
            while True:
                output = process.stdout.readline()
                if output:
                    text_area.insert(tk.END, output)
                    text_area.see(tk.END)
                if output == '' and process.poll() is not None:
                    break
            # Capture any remaining output from stderr
            stderr = process.stderr.read()
            if stderr:
                text_area.insert(tk.END, "\nErrors:\n" + stderr)
            process.wait()
            text_area.insert(tk.END, "\nPipeline complete!\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            run_button.config(state=tk.NORMAL)

    threading.Thread(target=task, daemon=True).start()

# Create the main window
root = tk.Tk()
root.title("Excel-SharePoint ETL Pipeline")

# Set the window size and optionally center it
root.geometry("800x500")

# Create a button that runs the pipeline
run_button = tk.Button(root, text="Run Pipeline", command=run_pipeline, font=("Arial", 14))
run_button.pack(pady=10)

# Create a scrollable text area for displaying logs
text_area = scrolledtext.ScrolledText(root, width=100, height=25, font=("Consolas", 10))
text_area.pack(padx=10, pady=10)

# Start the Tkinter event loop
root.mainloop()
