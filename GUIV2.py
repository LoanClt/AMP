import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
import copy
from simu_AMP import simu_AMP1, simu_AMP, bilan_puissance
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from io import StringIO
import sys


class JSONConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Laser Configuration Editor")
        self.root.geometry("1200x800")

        # Load initial configuration
        self.original_config = self.load_config()
        self.current_config = copy.deepcopy(self.original_config)

        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(expand=True, fill='both', padx=10, pady=5)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(expand=True, fill='both')

        # Create tabs for each amplifier
        self.tabs = {}
        self.entry_fields = {}

        for amp in ['AMP1', 'AMP2', 'AMP3']:
            self.create_amplifier_tab(amp)

        # Create BILAN_PUISSANCE tab
        self.create_bilan_puissance_tab()

        # Create Simulation tab
        self.create_simulation_tab()

        # Create buttons
        self.create_control_buttons()

    def load_config(self):
        try:
            with open('configTest.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Error", "Configuration file not found!")
            return {}

    def save_config(self):
        try:
            with open('configTest.json', 'w') as file:
                json.dump(self.current_config, file, indent=4)
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def create_amplifier_tab(self, amp_name):
        # Create tab
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=amp_name)
        self.tabs[amp_name] = tab
        self.entry_fields[amp_name] = {}

        # Create canvas with scrollbar
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Get configuration sections excluding RESULTATS
        sections = {k: v for k, v in self.current_config[amp_name].items() if k != 'RESULTATS'}

        # Create sections
        row = 0
        for section_name, section_data in sections.items():
            # Section header
            ttk.Label(scrollable_frame, text=section_name, font=('Arial', 12, 'bold')).grid(
                row=row, column=0, columnspan=2, pady=10, padx=5, sticky='w'
            )
            row += 1

            # Create entry fields for each parameter
            for param_name, param_value in section_data.items():
                ttk.Label(scrollable_frame, text=param_name).grid(
                    row=row, column=0, padx=5, pady=2, sticky='w'
                )

                entry = ttk.Entry(scrollable_frame, width=30)
                entry.insert(0, str(param_value))
                entry.grid(row=row, column=1, padx=5, pady=2)

                # Store entry field reference
                if section_name not in self.entry_fields[amp_name]:
                    self.entry_fields[amp_name][section_name] = {}
                self.entry_fields[amp_name][section_name][param_name] = entry

                row += 1

    def create_bilan_puissance_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="BILAN_PUISSANCE")
        self.entry_fields['BILAN_PUISSANCE'] = {}

        row = 0
        bilan_data = {k: v for k, v in self.current_config['BILAN_PUISSANCE'].items()
                      if k != 'PUISSANCE'}

        for param_name, param_value in bilan_data.items():
            ttk.Label(tab, text=param_name).grid(
                row=row, column=0, padx=5, pady=2, sticky='w'
            )

            entry = ttk.Entry(tab, width=30)
            entry.insert(0, str(param_value))
            entry.grid(row=row, column=1, padx=5, pady=2)

            self.entry_fields['BILAN_PUISSANCE'][param_name] = entry

            row += 1

    def create_simulation_tab(self):
        # Create simulation tab
        self.sim_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sim_tab, text="Simulation")

        # Create left panel for controls
        left_panel = ttk.Frame(self.sim_tab)
        left_panel.pack(side='left', fill='y', padx=10, pady=5)

        # Add simulation controls
        ttk.Label(left_panel, text="Simulation Parameters", font=('Arial', 12, 'bold')).pack(pady=5)

        # Number of points input
        n_points_frame = ttk.Frame(left_panel)
        n_points_frame.pack(fill='x', pady=5)
        ttk.Label(n_points_frame, text="Number of Points:").pack(side='left')
        self.n_points_entry = ttk.Entry(n_points_frame, width=10)
        self.n_points_entry.insert(0, "1000")
        self.n_points_entry.pack(side='left', padx=5)

        # Checkboxes for display options
        self.show_graphics_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_panel, text="Show Graphics",
                        variable=self.show_graphics_var).pack(pady=5)

        self.show_info_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_panel, text="Show Information",
                        variable=self.show_info_var).pack(pady=5)

        # Simulate button
        ttk.Button(left_panel, text="Simulate",
                   command=self.run_simulation).pack(pady=20)

        # Create right panel for results
        self.right_panel = ttk.Frame(self.sim_tab)
        self.right_panel.pack(side='right', fill='both', expand=True, padx=10, pady=5)

        # Create notebook for results
        self.results_notebook = ttk.Notebook(self.right_panel)
        self.results_notebook.pack(fill='both', expand=True)

        # Create tabs for each type of result
        self.table_frame = ttk.Frame(self.results_notebook)
        self.graph_frame = ttk.Frame(self.results_notebook)

        self.results_notebook.add(self.table_frame, text="Results Table")
        self.results_notebook.add(self.graph_frame, text="Graphs")

        # Text widget for table results
        self.table_text = tk.Text(self.table_frame, wrap=tk.WORD, height=20)
        self.table_text.pack(fill='both', expand=True)

    def create_simulation_tab(self):
        # Create simulation tab
        self.sim_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sim_tab, text="Simulation")

        # Create left panel for controls
        left_panel = ttk.Frame(self.sim_tab)
        left_panel.pack(side='left', fill='y', padx=10, pady=5)

        # Add simulation controls
        ttk.Label(left_panel, text="Simulation Parameters", font=('Arial', 12, 'bold')).pack(pady=5)

        # Number of points input
        n_points_frame = ttk.Frame(left_panel)
        n_points_frame.pack(fill='x', pady=5)
        ttk.Label(n_points_frame, text="Number of Points:").pack(side='left')
        self.n_points_entry = ttk.Entry(n_points_frame, width=10)
        self.n_points_entry.insert(0, "1000")
        self.n_points_entry.pack(side='left', padx=5)

        # Checkboxes for display options
        self.show_graphics_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_panel, text="Show Graphics",
                        variable=self.show_graphics_var).pack(pady=5)

        self.show_info_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_panel, text="Show Information",
                        variable=self.show_info_var).pack(pady=5)

        # Simulate button
        ttk.Button(left_panel, text="Simulate",
                   command=self.run_simulation).pack(pady=20)

        # Create right panel for results
        self.right_panel = ttk.Frame(self.sim_tab)
        self.right_panel.pack(side='right', fill='both', expand=True, padx=10, pady=5)

        # Create notebook for results
        self.results_notebook = ttk.Notebook(self.right_panel)
        self.results_notebook.pack(fill='both', expand=True)

        # Create tabs for each type of result
        self.table_frame = ttk.Frame(self.results_notebook)
        self.graph_frame = ttk.Frame(self.results_notebook)

        self.results_notebook.add(self.table_frame, text="Results Table")
        self.results_notebook.add(self.graph_frame, text="Graphs")

        # Create a canvas with scrollbar for the table frame
        self.table_canvas = tk.Canvas(self.table_frame)
        table_scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical",
                                        command=self.table_canvas.yview)
        table_scrollbar_x = ttk.Scrollbar(self.table_frame, orient="horizontal",
                                          command=self.table_canvas.xview)

        self.table_scroll_frame = ttk.Frame(self.table_canvas)

        self.table_scroll_frame.bind(
            "<Configure>",
            lambda e: self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))
        )

        self.table_canvas.create_window((0, 0), window=self.table_scroll_frame, anchor="nw")
        self.table_canvas.configure(yscrollcommand=table_scrollbar.set,
                                    xscrollcommand=table_scrollbar_x.set)

        # Pack scrollbars and canvas
        table_scrollbar.pack(side="right", fill="y")
        table_scrollbar_x.pack(side="bottom", fill="x")
        self.table_canvas.pack(side="left", fill="both", expand=True)

        # Create text widgets for each amplifier's results
        self.amp_results = {}
        for amp in ['AMP1', 'AMP2', 'AMP3']:
            frame = ttk.LabelFrame(self.table_scroll_frame, text=f"{amp} Results")
            frame.pack(fill='both', expand=True, padx=5, pady=5)

            text_widget = tk.Text(frame, wrap=tk.NONE, height=15)
            text_widget.pack(fill='both', expand=True)

            # Add horizontal scrollbar for each text widget
            h_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
            h_scrollbar.pack(fill='x')
            text_widget.configure(xscrollcommand=h_scrollbar.set)

            self.amp_results[amp] = text_widget

    def run_simulation(self):
        try:
            # Save current configuration before simulation
            self.update_config()

            # Get simulation parameters and convert n_points to integer
            try:
                n_points = int(self.n_points_entry.get())
                if n_points <= 0:
                    raise ValueError("Number of points must be positive")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid number of points: {str(e)}")
                return

            show_graphics = self.show_graphics_var.get()
            show_info = self.show_info_var.get()

            # Clear previous results
            for text_widget in self.amp_results.values():
                text_widget.delete(1.0, tk.END)

            for widget in self.graph_frame.winfo_children():
                widget.destroy()

            # Close any existing matplotlib figures
            plt.close('all')

            # Function to capture stdout and return it
            def capture_output(func, *args):
                stdout = StringIO()
                sys.stdout = stdout
                result = func(*args)
                sys.stdout = sys.__stdout__
                return result, stdout.getvalue()

            # Run simulations and capture outputs
            (data, passage, abscisse_df), amp1_output = capture_output(
                simu_AMP1, "configTest.json", n_points, show_graphics, show_info
            )
            self.amp_results['AMP1'].insert(tk.END, amp1_output)

            (data, passage, abscisse_df), amp2_output = capture_output(
                simu_AMP, "configTest.json", passage, abscisse_df, "2", n_points, show_graphics, show_info
            )
            self.amp_results['AMP2'].insert(tk.END, amp2_output)

            (data, passage, abscisse_df), amp3_output = capture_output(
                simu_AMP, "configTest.json", passage, abscisse_df, "3", n_points, show_graphics, show_info
            )
            self.amp_results['AMP3'].insert(tk.END, amp3_output)

            # Calculate power balance
            _, power_output = capture_output(
                bilan_puissance, "configTest.json", show_info
            )

            # Make all text widgets read-only
            for text_widget in self.amp_results.values():
                text_widget.config(state='disabled')

            # If graphics were generated, display them in the graph tab
            if show_graphics:
                figures = [plt.figure(num) for num in plt.get_fignums()]
                for i, fig in enumerate(figures):
                    frame = ttk.Frame(self.graph_frame)
                    frame.pack(fill='both', expand=True)
                    canvas = FigureCanvasTkAgg(fig, master=frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill='both', expand=True)

            messagebox.showinfo("Success", "Simulation completed successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed: {str(e)}")
            import traceback
            print("Error traceback:")
            traceback.print_exc()

    def create_control_buttons(self):
        button_frame = ttk.Frame(self.main_container)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text="Save Changes",
                   command=self.update_config).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Reset to Original",
                   command=self.reset_config).pack(side='left', padx=5)

    def update_config(self):
        try:
            # Update amplifier configurations
            for amp_name in ['AMP1', 'AMP2', 'AMP3']:
                for section_name, section_fields in self.entry_fields[amp_name].items():
                    for param_name, entry in section_fields.items():
                        value = entry.get()
                        # Convert to appropriate type
                        try:
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            # Keep as string if conversion fails (e.g., for scientific notation)
                            if value.lower() in ['true', 'false']:
                                value = value.lower() == 'true'
                            # Handle scientific notation
                            elif 'e' in value.lower():
                                try:
                                    value = float(value)
                                except ValueError:
                                    pass
                        self.current_config[amp_name][section_name][param_name] = value

            # Update BILAN_PUISSANCE configuration
            for param_name, entry in self.entry_fields['BILAN_PUISSANCE'].items():
                value = entry.get()
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
                self.current_config['BILAN_PUISSANCE'][param_name] = value

            self.save_config()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update configuration: {str(e)}")
            raise

    def reset_config(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all values to original?"):
            self.current_config = copy.deepcopy(self.original_config)
            # Reset all entry fields
            for amp_name in ['AMP1', 'AMP2', 'AMP3']:
                for section_name, section_fields in self.entry_fields[amp_name].items():
                    for param_name, entry in section_fields.items():
                        entry.delete(0, tk.END)
                        entry.insert(0, str(self.original_config[amp_name][section_name][param_name]))

            for param_name, entry in self.entry_fields['BILAN_PUISSANCE'].items():
                entry.delete(0, tk.END)
                entry.insert(0, str(self.original_config['BILAN_PUISSANCE'][param_name]))

def configEditor():
    root = tk.Tk()
    app = JSONConfigEditor(root)
    root.mainloop()


if __name__ == "__main__":
    configEditor()