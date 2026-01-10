import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
import threading
import time
import logging
from unittest.mock import MagicMock
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, project_root)
try:
    from main import MainApplication
    from config import Config
except ImportError as e:
    print(f'CRITICAL ERROR: Could not import main application: {e}')
    sys.exit(1)

class MacroRunner(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('X-Annotation Macro Runner V2')
        self.geometry('800x600')
        self.app_window = None
        self.app_instance = None
        self.log_file = os.path.join(project_root, 'application.log')
        self.last_log_pos = 0
        self.errors_found = []
        self.safe_mode = True
        self.blacklist = ['delete', 'remove', 'excluir', 'apagar', 'deletar', 'sair', 'close', 'cancel', 'cancelar']
        self._setup_ui()

    def _setup_ui(self):
        lbl_header = ttk.Label(self, text='Automated Deep GUI Tester', font=('Helvetica', 16, 'bold'))
        lbl_header.pack(pady=10)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        self.btn_run = ttk.Button(btn_frame, text='Start Deep Scan', command=self.start_test)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        self.chk_safe_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(btn_frame, text='Safe Mode (No Destructive Clicks)', variable=self.chk_safe_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Close Runner', command=self.destroy).pack(side=tk.LEFT, padx=5)
        self.txt_status = scrolledtext.ScrolledText(self, width=90, height=25)
        self.txt_status.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.txt_status.tag_config('pass', foreground='green')
        self.txt_status.tag_config('fail', foreground='red')
        self.txt_status.tag_config('info', foreground='blue')
        self.txt_status.tag_config('warn', foreground='orange')

    def log(self, message, tag='info'):
        self.txt_status.insert(tk.END, f'{message}\n', tag)
        self.txt_status.see(tk.END)
        self.update_idletasks()

    def start_test(self):
        self.btn_run.config(state='disabled')
        self.safe_mode = self.chk_safe_var.get()
        self.txt_status.delete(1.0, tk.END)
        self.errors_found = []
        self.log(f'Starting Deep Scan (Safe Mode: {self.safe_mode})...', 'info')
        if os.path.exists(self.log_file):
            self.last_log_pos = os.path.getsize(self.log_file)
        self.log('Initializing Application...', 'info')
        try:
            self._mock_dialogs()
            self.app_window = tk.Toplevel(self)
            self.app_window.title('App Under Test')
            self.app_instance = MainApplication(self.app_window)
            self.after(1000, self.step_1_main_window_scan)
        except Exception as e:
            self.log(f'CRITICAL: Failed to launch app: {e}', 'fail')
            self.btn_run.config(state='normal')

    def _mock_dialogs(self):

        def auto_ok(*args, **kwargs):
            self.log(f'  [Mock] Dialog suppressed: {args}', 'info')
            return 'yes'
        import tkinter.messagebox
        self.original_askyesno = tkinter.messagebox.askyesno
        self.original_showinfo = tkinter.messagebox.showinfo
        self.original_showwarning = tkinter.messagebox.showwarning
        self.original_showerror = tkinter.messagebox.showerror
        tkinter.messagebox.askyesno = auto_ok
        tkinter.messagebox.showinfo = auto_ok
        tkinter.messagebox.showwarning = auto_ok
        tkinter.messagebox.showerror = auto_ok

    def check_logs(self):
        if not os.path.exists(self.log_file):
            return
        current_size = os.path.getsize(self.log_file)
        if current_size > self.last_log_pos:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(self.last_log_pos)
                new_liens = f.readlines()
                self.last_log_pos = current_size
                for line in new_liens:
                    if 'ERROR' in line or 'CRITICAL' in line or 'Exception' in line:
                        self.log(f'LOG ERROR: {line.strip()}', 'fail')
                        self.errors_found.append(line)

    def walk_and_poke(self, widget, depth=0):
        indent = '  ' * (depth + 2)
        children = widget.winfo_children()
        for child in children:
            try:
                if isinstance(child, ttk.Notebook):
                    self.log(f'{indent}[Notebook] Found {len(child.tabs())} tabs.', 'info')
                    self._test_notebook_tabs(child, depth)
                elif isinstance(child, (ttk.Button, tk.Button)):
                    text = str(child.cget('text')).strip()
                    self.log(f"{indent}[Button] Found: '{text}' state={str(child['state'])}", 'info')
                self.walk_and_poke(child, depth + 1)
            except Exception as e:
                self.log(f'{indent}WARNING: Error inspecting widget {child}: {e}', 'warn')

    def _test_notebook_tabs(self, notebook, depth):
        indent = '  ' * (depth + 3)
        tabs = notebook.tabs()
        for i, tab_id in enumerate(tabs):
            try:
                notebook.select(tab_id)
                try:
                    tab_text = notebook.tab(tab_id, 'text')
                except:
                    tab_text = f'Tab {i}'
                self.log(f"{indent}-> Switched to Tab: '{tab_text}'", 'info')
                self.app_window.update_idletasks()
                self.check_logs()
                time.sleep(0.2)
            except Exception as e:
                self.log(f'{indent}FAILED to switch tab {i}: {e}', 'fail')
                self.errors_found.append(f'Tab switch error: {e}')

    def close_active_toplevel(self, next_step):
        target = None
        for widget in self.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget != self.app_window:
                target = widget
        if not target and self.app_window:
            for widget in self.app_window.winfo_children():
                if isinstance(widget, tk.Toplevel):
                    target = widget
        if target:
            self.log(f"  Walking window '{target.title()}' before closing...", 'info')
            self.walk_and_poke(target)
            self.log(f'  Closing window: {target.title()}', 'info')
            target.destroy()
        else:
            self.log('  WARNING: No popup window found to close.', 'warn')
        self.check_logs()
        self.after(500, next_step)

    def step_1_main_window_scan(self):
        self.log('Step 1: Scanning Main Window...', 'info')
        self.walk_and_poke(self.app_window)
        found_combo = False
        try:
            for widget in self.app_instance.ui.root.winfo_children():
                pass
            if hasattr(self.app_instance.ui, 'lang_combo'):
                self.log('  [Check] Language Combobox found in UI manager.', 'pass')
                found_combo = True
            else:
                self.log('  [Check] WARNING: Language Combobox NOT found in UI manager.', 'warn')
        except Exception as e:
            self.log(f'  [Check] Error verifying combobox: {e}', 'warn')
        self.check_logs()
        self.after(1000, self.step_2_open_grid)

    def step_2_open_grid(self):
        self.log("Step 2: Testing 'Grade' (Visualizador)...", 'info')
        try:
            self.app_instance.open_grid_viewer()
            self.check_logs()
            self.after(1500, lambda: self.close_active_toplevel(self.step_3_open_stats))
        except Exception as e:
            self.log(f'FAILED Step 2: {e}', 'fail')
            self.errors_found.append(str(e))
            self.after(1000, self.step_3_open_stats)

    def step_3_open_stats(self):
        self.log("Step 3: Testing 'Análise' (Stats) [Deep Tab Scan]...", 'info')
        try:
            self.app_instance.open_dataset_analyzer()
            self.check_logs()
            self.after(1500, lambda: self.close_active_toplevel(self.step_4_open_split))
        except Exception as e:
            self.log(f'FAILED Step 3: {e}', 'fail')
            self.errors_found.append(str(e))
            self.after(1000, self.step_4_open_split)

    def step_4_open_split(self):
        self.log("Step 4: Testing 'Divisão' (Split)...", 'info')
        try:
            self.app_instance.open_split_wizard()
            self.check_logs()
            self.after(1000, lambda: self.close_active_toplevel(self.step_5_open_classes))
        except Exception as e:
            self.log(f'FAILED Step 4: {e}', 'fail')
            self.errors_found.append(str(e))
            self.after(1000, self.step_5_open_classes)

    def step_5_open_classes(self):
        self.log("Step 5: Testing 'Gerenciar Classes'...", 'info')
        try:
            self.app_instance.open_class_manager()
            self.check_logs()
            self.after(1000, lambda: self.close_active_toplevel(self.step_6_open_about))
        except Exception as e:
            self.log(f'FAILED Step 5: {e}', 'fail')
            self.errors_found.append(str(e))
            self.after(1000, self.step_6_open_about)

    def step_6_open_about(self):
        self.log("Step 6: Testing 'Sobre' (About Dialog)...", 'info')
        try:
            self.app_instance.show_about_dialog()
            self.check_logs()
            self.after(1000, lambda: self.close_active_toplevel(self.finish_test))
        except Exception as e:
            self.log(f'FAILED Step 6: {e}', 'fail')
            self.errors_found.append(str(e))
            self.after(1000, self.finish_test)

    def finish_test(self):
        self.log('-' * 40, 'info')
        if not self.errors_found:
            self.log('DEEP SCAN COMPLETED: SUCCESS', 'pass')
            messagebox.showinfo('Scanner Result', 'All tests passed. No application crashes or errors detected.')
        else:
            self.log(f'DEEP SCAN COMPLETED: {len(self.errors_found)} ERRORS FOUND', 'fail')
            messagebox.showwarning('Scanner Result', 'Errors were detected. Check the log details.')
        import tkinter.messagebox
        tkinter.messagebox.askyesno = self.original_askyesno
        tkinter.messagebox.showinfo = self.original_showinfo
        tkinter.messagebox.showwarning = self.original_showwarning
        tkinter.messagebox.showerror = self.original_showerror
        if self.app_window:
            self.app_window.destroy()
        self.btn_run.config(state='normal')
if __name__ == '__main__':
    app = MacroRunner()
    if '--auto' in sys.argv:
        app.after(500, app.start_test)
    app.mainloop()