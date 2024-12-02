import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import ImageTk, Image
import json
from pathlib import Path
import copy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from io import StringIO, BytesIO  # Added BytesIO
import sys
from simu_AMP import simu_AMP1, simu_AMP, bilan_puissance
import os

# Imports for PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class JSONConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Laser Amplification Simulation")
        self.root.geometry("1200x800")

        # Add number of amplifiers attribute
        self.num_amps = None

        self.original_config = None
        self.current_config = None
        self.config_file_path = None

        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(expand=True, fill='both', padx=10, pady=5)

        # Start with dialog instead of welcome screen
        self.create_amp_selection_dialog()

        self.notebook = None
        self.tabs = {}
        self.entry_fields = {}
        self.sim_tab = None
        self.results_notebook = None

    def create_amp_selection_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Number of Amplifiers")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog,
                  text="Select the number of amplifier stages (2-6):",
                  wraplength=250,
                  justify="center").pack(pady=10)

        var = tk.StringVar(value="3")
        combo = ttk.Combobox(dialog,
                             textvariable=var,
                             values=["2", "3", "4", "5", "6"],
                             state="readonly",
                             width=5)
        combo.pack(pady=10)

        def on_ok():
            self.num_amps = int(var.get())
            dialog.destroy()
            self.create_welcome_screen()

        ttk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

        # Center the dialog on the screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")

    def create_welcome_screen(self):
        self.welcome_frame = ttk.Frame(self.main_container)
        self.welcome_frame.pack(expand=True, fill='both')

        welcome_label = ttk.Label(
            self.welcome_frame,
            text=f"Laser Amplification Simulation (v.0.1)\nConfigured for {self.num_amps} amplifier stages\nPlease load a configuration file to begin\n\nMade by Loan Challeat\nContact: loan.challeat@thalesgroup.com",
            font=('Arial', 14),
            justify='center'
        )
        welcome_label.pack(expand=True, pady=10)

        load_button = ttk.Button(
            self.welcome_frame,
            text="Load Configuration",
            command=self.load_configuration
        )
        load_button.pack(pady=20)

    def load_configuration(self):
        file_path = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r') as file:
                    config = json.load(file)

                # Check for required AMP sections based on num_amps
                required_sections = [f'AMP{i}' for i in range(1, self.num_amps + 1)] + ['BILAN_PUISSANCE']
                if not all(section in config for section in required_sections):
                    raise ValueError("Invalid configuration file format: Missing required sections")

                self.config_file_path = file_path
                self.original_config = copy.deepcopy(config)
                self.current_config = copy.deepcopy(config)

                self.welcome_frame.destroy()
                self.create_main_ui()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

    def create_main_ui(self):
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(expand=True, fill='both')

        # Create only the requested number of AMP tabs
        for amp in range(1, self.num_amps + 1):
            self.create_amplifier_tab(f"AMP{amp}")

        self.create_bilan_puissance_tab()
        self.create_simulation_tab()
        self.create_control_buttons()
        self.create_status_bar()

    def create_status_bar(self):
        self.status_bar = ttk.Frame(self.main_container)
        self.status_bar.pack(fill='x', pady=(5, 0))

        self.file_label = ttk.Label(
            self.status_bar,
            text=f"Current file: {Path(self.config_file_path).name}",
            font=('Arial', 9)
        )
        self.file_label.pack(side='right', padx=10, pady=2)

    def update_file_label(self):
        if hasattr(self, 'file_label'):
            self.file_label.config(text=f"Current file: {Path(self.config_file_path).name}")

    def create_amplifier_tab(self, amp_name):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=amp_name)
        self.tabs[amp_name] = tab
        self.entry_fields[amp_name] = {}

        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        sections = {k: v for k, v in self.current_config[amp_name].items() if k != 'RESULTATS'}

        style = ttk.Style()
        style.configure("Section.TLabel", font=('Arial', 12, 'bold'), padding=10)
        style.configure("Param.TLabel", font=('Arial', 10), padding=5)

        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        ttk.Label(header_frame,
                  text=f"{amp_name} Configuration",
                  font=('Arial', 14, 'bold')).pack()

        columns_frame = ttk.Frame(scrollable_frame)
        columns_frame.pack(fill='both', expand=True, padx=20, pady=10)

        left_column = ttk.Frame(columns_frame)
        right_column = ttk.Frame(columns_frame)
        left_column.pack(side='left', fill='both', expand=True, padx=10)
        right_column.pack(side='right', fill='both', expand=True, padx=10)

        section_list = list(sections.items())
        mid_point = len(section_list) // 2

        for section_name, section_data in section_list[:mid_point]:
            self.create_section(left_column, amp_name, section_name, section_data)

        for section_name, section_data in section_list[mid_point:]:
            self.create_section(right_column, amp_name, section_name, section_data)

    def create_section(self, parent, amp_name, section_name, section_data):
        """Create a section frame with parameters"""
        # Parameters modifiable only in AMP1
        amp1_only_params = {
            "FAISCEAU_IR": [
                "ENERGIE",
                "LARGEUR_SPECTRALE",  # Only LARGEUR_SPECTRALE in FAISCEAU_IR section
                "LONGUEUR_ONDE_CENTRALE_LC",
                "DUREE_ETIREE"
            ]
        }

        # Parameters modifiable in all amplifiers
        editable_params = [
            "PROFIL_SPATIAL",
            "DIAMETRE",
            "PROFIL_TEMPORAL",
            "GEOMETRIE_AMPLIFICATEUR",
            "PASSAGES",
            "COTES_POMPAGE",
            "FEEDBACK",
            "SEUIL_DOMMAGE",
            "IR_POMPE",
            "PERTES_APRES_PASSAGE",
            "DIAMETRE",
            "LONGUEUR",
            "ABSORPTION_A_532NM",
            "TEMPERATURE_CRISTAL",
            "OUI_NON",
            "PROFIL_SPECTRAL",
            "LARGEUR_SPECTRALE",  # This will apply to FILTRE_SPECTRAL section
            "LONGUEUR_ONDE_CENTRALE",
            "TRANSMISSION_SPECTRALE",
            "ENERGIE_FACE",
            "PROFIL_SPATIAL",
            "TAUX_REPETITION",
            "DUREE",
            "LONGUEUR_ONDE_LP"
        ]

        section_frame = ttk.LabelFrame(parent, text=section_name, padding=(10, 5))
        section_frame.pack(fill='x', padx=5, pady=5, ipadx=5, ipady=5)

        param_frame = ttk.Frame(section_frame)
        param_frame.pack(fill='x', expand=True)

        param_frame.grid_columnconfigure(1, weight=1)

        for row, (param_name, param_value) in enumerate(section_data.items()):
            # Determine if parameter should be editable
            is_editable = param_name in editable_params

            # Special handling for LARGEUR_SPECTRALE in FAISCEAU_IR
            if param_name == "LARGEUR_SPECTRALE":
                if section_name == "FAISCEAU_IR":
                    # In FAISCEAU_IR, only editable in AMP1
                    is_editable = amp_name == "AMP1"
                else:
                    # In other sections (like FILTRE_SPECTRAL), always editable
                    is_editable = True
            # Handle other AMP1-only parameters
            elif section_name in amp1_only_params and param_name in amp1_only_params[section_name]:
                is_editable = amp_name == "AMP1"

            # Create parameter name label (bold if editable)
            name_label = ttk.Label(param_frame, 
                                 text=param_name,
                                 font=('Arial', 10, 'bold') if is_editable else ('Arial', 10))
            name_label.grid(row=row, column=0, padx=(5, 10), pady=2, sticky="w")
            self.create_tooltip(name_label, f"Parameter: {param_name}")

            if is_editable:
                # Create entry field for editable parameters
                entry = ttk.Entry(param_frame, width=20)
                entry.insert(0, str(param_value))
                entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
                self.setup_entry_validation(entry, param_name, param_value)

                if section_name not in self.entry_fields[amp_name]:
                    self.entry_fields[amp_name][section_name] = {}
                self.entry_fields[amp_name][section_name][param_name] = entry
            else:
                # Create read-only label for non-editable parameters
                value_label = ttk.Label(param_frame, text=str(param_value))
                value_label.grid(row=row, column=1, padx=5, pady=2, sticky="w")

                # Store the label in entry_fields for updating
                if section_name not in self.entry_fields[amp_name]:
                    self.entry_fields[amp_name][section_name] = {}
                self.entry_fields[amp_name][section_name][param_name] = value_label

            # Add units if applicable
            unit = self.get_parameter_unit(param_name)
            if unit:
                ttk.Label(param_frame, text=unit).grid(row=row, column=2, padx=(2, 5), pady=2)

    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            label = ttk.Label(tooltip, text=text, justify='left',
                              background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()

            def hide_tooltip():
                tooltip.destroy()

            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())

        widget.bind('<Enter>', show_tooltip)

    def setup_entry_validation(self, entry, param_name, default_value):
        def validate_input(value):
            if not value:
                return True
            try:
                if isinstance(default_value, int):
                    int(value)
                elif isinstance(default_value, float):
                    float(value)
                return True
            except ValueError:
                if 'e' in value.lower():
                    try:
                        float(value)
                        return True
                    except ValueError:
                        return False
                return False

        def on_focus_out(event):
            value = entry.get()
            if value:
                try:
                    if isinstance(default_value, float):
                        formatted = f"{float(value):.6g}"
                        entry.delete(0, tk.END)
                        entry.insert(0, formatted)
                except ValueError:
                    pass

        validate_cmd = entry.register(validate_input)
        entry.config(validate='key', validatecommand=(validate_cmd, '%P'))
        entry.bind('<FocusOut>', on_focus_out)

    def get_parameter_unit(self, param_name):
        units = {
            'LINEAR': 'm-1',
            '_DOMMAGE': '%',
            'ENERGIE': 'mJ',
            'DIAMETRE': 'mm',
            'LONGUEUR': 'nm',
            'DUREE': 'ps',
            'TEMPERATURE': 'K',
            'FREQUENCE': 'Hz',
            'PUISSANCE': 'W',
            'LARGEUR_SPECTRALE': 'nm',
            'REPETITION': 'Hz',
            'ECLAIREMENT': 'MW/cm2',
            'CHIRP': 's-2',
            'WAIST': 'mm',
            'RAYON': 'mm',
            'SURFACE': 'cm2',
            '_IR': 'J/cm2',
            '_POMPE': 'J/cm2',
            'ABSORPTION': '%',
            'SATURATION': '%',
            'SEUIL': 'J/cm2',
            'IR_POMPE': '%',
            'PERTES': '%',
            'FOCALE': 'm',
            'CONDUC': 'W/m/K',
        }

        for key, unit in units.items():
            if key in param_name.upper():
                return unit
        return ''

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
        self.sim_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sim_tab, text="Simulation")
    
        left_panel = ttk.Frame(self.sim_tab)
        left_panel.pack(side='left', fill='y', padx=10, pady=5)
    
        ttk.Label(left_panel, text="Simulation Parameters",
                  font=('Arial', 12, 'bold')).pack(pady=5)
    
        n_points_frame = ttk.Frame(left_panel)
        n_points_frame.pack(fill='x', pady=5)
        ttk.Label(n_points_frame, text="Number of Points:").pack(side='left')
        self.n_points_entry = ttk.Entry(n_points_frame, width=10)
        self.n_points_entry.insert(0, "200")
        self.n_points_entry.pack(side='left', padx=5)
    
        self.show_graphics_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_panel, text="Show Graphics",
                        variable=self.show_graphics_var).pack(pady=5)
    
        self.show_info_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_panel, text="Show Information",
                        variable=self.show_info_var).pack(pady=5)
    
        # Create a frame for buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Simulate",
                   command=self.run_simulation).pack(pady=(0, 5))
        
        ttk.Button(button_frame, text="Save Report",
                   command=self.save_report).pack(pady=(5, 0))
    
        self.right_panel = ttk.Frame(self.sim_tab)
        self.right_panel.pack(side='right', fill='both', expand=True, padx=10, pady=5)
    
        self.results_notebook = ttk.Notebook(self.right_panel)
        self.results_notebook.pack(fill='both', expand=True)
    
        self.table_frame = ttk.Frame(self.results_notebook)
        self.graph_frame = ttk.Frame(self.results_notebook)
    
        self.results_notebook.add(self.table_frame, text="Results Table")
        self.results_notebook.add(self.graph_frame, text="Graphs")
    
        self.setup_table_frame()
        self.setup_graph_frame()

    def setup_table_frame(self):
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

        table_scrollbar.pack(side="right", fill="y")
        table_scrollbar_x.pack(side="bottom", fill="x")
        self.table_canvas.pack(side="left", fill="both", expand=True)

        self.amp_results = {}
        # Create text widgets only for the requested number of amplifiers
        for amp in range(1, self.num_amps + 1):
            amp_name = f"AMP{amp}"
            frame = ttk.LabelFrame(self.table_scroll_frame, text=f"{amp_name} Results")
            frame.pack(fill='both', expand=True, padx=5, pady=5)

            text_widget = tk.Text(frame, wrap=tk.NONE, height=15)
            text_widget.pack(fill='both', expand=True)

            h_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
            h_scrollbar.pack(fill='x')
            text_widget.configure(xscrollcommand=h_scrollbar.set)

            self.amp_results[amp_name] = text_widget

        power_frame = ttk.LabelFrame(self.table_scroll_frame, text="Power Balance")
        power_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.power_text = tk.Text(power_frame, wrap=tk.NONE, height=8, width=100)
        self.power_text.pack(fill='both', expand=True)

        power_h_scrollbar = ttk.Scrollbar(power_frame, orient="horizontal",
                                          command=self.power_text.xview)
        power_h_scrollbar.pack(fill='x')
        self.power_text.configure(xscrollcommand=power_h_scrollbar.set)

        verify_frame = ttk.LabelFrame(self.table_scroll_frame, text="System Verification")
        verify_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.verify_text = tk.Text(verify_frame, wrap=tk.NONE, height=8)
        self.verify_text.pack(fill='both', expand=True)

        verify_h_scrollbar = ttk.Scrollbar(verify_frame, orient="horizontal",
                                           command=self.verify_text.xview)
        verify_h_scrollbar.pack(fill='x')
        self.verify_text.configure(xscrollcommand=verify_h_scrollbar.set)

    def display_amp_graphs(self, amp_name, figures_dict):
        """Display graphs for an AMP stage"""
        frame = self.graph_frames[amp_name]
        
        # Clear any existing widgets in the frame
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create main container for this AMP's graphs
        amp_container = ttk.LabelFrame(frame, text=f"{amp_name} Results")
        amp_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create three columns for the graphs
        for i in range(3):
            amp_container.grid_columnconfigure(i, weight=1)
        
        # Create the graphs in the specific order
        graph_order = ['Spectrum', 'Gain', 'Energy']
        frame.canvases = []  # Store canvas references
        
        for i, title in enumerate(graph_order):
            plot_frame = ttk.Frame(amp_container)
            plot_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            # Add title for each graph
            ttk.Label(plot_frame, text=title, font=('Arial', 10, 'bold')).pack(pady=(0, 5))
            
            # Create and pack the canvas
            fig = figures_dict[title]
            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            frame.canvases.append(canvas)
    
    def setup_graph_frame(self):
        # Create main canvas with scrollbar
        self.graph_canvas = tk.Canvas(self.graph_frame)
        graph_scrollbar_y = ttk.Scrollbar(self.graph_frame, orient="vertical",
                                        command=self.graph_canvas.yview)
        graph_scrollbar_x = ttk.Scrollbar(self.graph_frame, orient="horizontal",
                                        command=self.graph_canvas.xview)
    
        # Create scrollable frame
        self.graph_scroll_frame = ttk.Frame(self.graph_canvas)
        
        # Configure scrolling
        self.graph_scroll_frame.bind(
            "<Configure>",
            lambda e: self.graph_canvas.configure(scrollregion=self.graph_canvas.bbox("all"))
        )
    
        # Create window in canvas
        self.graph_canvas.create_window((0, 0), window=self.graph_scroll_frame, anchor="nw")
        self.graph_canvas.configure(yscrollcommand=graph_scrollbar_y.set,
                                  xscrollcommand=graph_scrollbar_x.set)
    
        # Pack scrollbars and canvas
        graph_scrollbar_y.pack(side="right", fill="y")
        graph_scrollbar_x.pack(side="bottom", fill="x")
        self.graph_canvas.pack(side="left", fill="both", expand=True)
    
        # Create frames for each AMP
        self.graph_frames = {}
        for i in range(1, self.num_amps + 1):
            frame = ttk.Frame(self.graph_scroll_frame)
            frame.pack(fill='both', expand=True, padx=5, pady=5)
            self.graph_frames[f"AMP{i}"] = frame
    
    def run_simulation(self):
        if not self.config_file_path:
            messagebox.showerror("Error", "No configuration file loaded")
            return
    
        try:
            self.update_config()
    
            try:
                n_points = int(self.n_points_entry.get())
                if n_points <= 0:
                    raise ValueError("Number of points must be positive")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid number of points: {str(e)}")
                return
    
            show_graphics = self.show_graphics_var.get()
            show_info = self.show_info_var.get()
    
            # Clear all results and graphs
            self.clear_results()
    
            def capture_output(func, *args):
                stdout = StringIO()
                sys.stdout = stdout
                result = func(*args)
                sys.stdout = sys.__stdout__
                return result, stdout.getvalue()
    
            all_figures = {}
            self.simulation_results = {'figures': {}, 'outputs': {}}  # Store results as class attribute
    
            # Run AMP1 simulation
            plt.close('all')
            (data, passage, abscisse_df), amp1_output = capture_output(
                simu_AMP1, self.config_file_path, n_points, show_graphics, show_info
            )
            self.amp_results['AMP1'].insert(tk.END, amp1_output)
            self.simulation_results['outputs']['AMP1'] = amp1_output
            
            if show_graphics:
                figures = [plt.figure(num) for num in plt.get_fignums()]
                if figures:
                    all_figures['AMP1'] = {
                        'Spectrum': figures[0],
                        'Gain': figures[1],
                        'Energy': figures[2]
                    }
                    self.simulation_results['figures']['AMP1'] = all_figures['AMP1']
    
            # Run subsequent AMP simulations
            for amp_num in range(2, self.num_amps + 1):
                plt.close('all')
                (data, passage, abscisse_df), amp_output = capture_output(
                    simu_AMP, self.config_file_path, passage, abscisse_df, 
                    str(amp_num), n_points, show_graphics, show_info
                )
                amp_name = f'AMP{amp_num}'
                self.amp_results[amp_name].insert(tk.END, amp_output)
                self.simulation_results['outputs'][amp_name] = amp_output
                
                if show_graphics:
                    figures = [plt.figure(num) for num in plt.get_fignums()]
                    if figures:
                        all_figures[amp_name] = {
                            'Spectrum': figures[0],
                            'Gain': figures[1],
                            'Energy': figures[2]
                        }
                        self.simulation_results['figures'][amp_name] = all_figures[amp_name]
    
            # Calculate power balance
            _, power_output = capture_output(
                bilan_puissance, self.config_file_path, show_info, self.num_amps
            )
            self.power_text.insert(tk.END, power_output)
            self.simulation_results['power_balance'] = power_output
    
            # Run verification
            from error_checker import verification
            _, verify_output = capture_output(
                verification, self.config_file_path, show_info, self.num_amps
            )
            self.verify_text.insert(tk.END, verify_output)
            self.simulation_results['verification'] = verify_output
    
            # Display all figures for all AMPs
            if show_graphics:
                for amp_name, figures_dict in all_figures.items():
                    self.display_amp_graphs(amp_name, figures_dict)
    
            # Disable text widgets and show graphs
            self.disable_text_widgets()
            if show_graphics:
                self.results_notebook.select(1)
    
            plt.close('all')
            messagebox.showinfo("Success", "Simulation completed successfully!")
    
        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def save_report(self):
        """Generate and save a PDF report of the simulation results"""
        if not hasattr(self, 'simulation_results'):
            messagebox.showerror("Error", "No simulation results available. Please run a simulation first.")
            return
            
        try:
            # Get save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile="simulation_report.pdf"
            )
            
            if not file_path:
                return
    
            # Create the PDF document
            doc = SimpleDocTemplate(
                file_path,
                pagesize=landscape(A4),
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
    
            # Container for PDF elements and image buffers
            elements = []
            buffers = []  # Keep track of buffers
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            
            # Add title
            elements.append(Paragraph("Laser Amplification Simulation Report", title_style))
            elements.append(Spacer(1, 20))
    
            # Add configuration file info
            elements.append(Paragraph(f"Configuration file: {os.path.basename(self.config_file_path)}", styles['Normal']))
            elements.append(Spacer(1, 20))
    
            # Process each AMP's results
            for amp_num in range(1, self.num_amps + 1):
                amp_name = f"AMP{amp_num}"
                
                # Add AMP title
                elements.append(Paragraph(f"{amp_name} Results", styles['Heading2']))
                elements.append(Spacer(1, 10))
    
                # Get text results from stored simulation results
                text_content = self.simulation_results['outputs'].get(amp_name, '')
                if text_content:
                    # Create table from text results
                    rows = []
                    for line in text_content.split('\n'):
                        if line.strip():
                            rows.append([line])
                    
                    if rows:
                        table = Table(rows, colWidths=[500])
                        table.setStyle(TableStyle([
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 10))
    
                # Add figures if they exist
                if amp_name in self.simulation_results['figures']:
                    figures_dict = self.simulation_results['figures'][amp_name]
                    elements.append(Paragraph(f"{amp_name} Graphs", styles['Heading3']))
                    elements.append(Spacer(1, 10))
                    
                    for title, fig in figures_dict.items():
                        # Create a new buffer for each image
                        buf = BytesIO()
                        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                        buf.seek(0)
                        buffers.append(buf)  # Keep buffer reference
                        
                        # Add title for each graph
                        elements.append(Paragraph(title, styles['Heading4']))
                        elements.append(Spacer(1, 5))
                        
                        # Add image to PDF
                        img = RLImage(buf)
                        img.drawHeight = 2.5*inch
                        img.drawWidth = 3.5*inch
                        elements.append(img)
                        elements.append(Spacer(1, 10))
                
                elements.append(Spacer(1, 20))
    
            # Add power balance results
            if 'power_balance' in self.simulation_results:
                elements.append(Paragraph("Power Balance Results", styles['Heading2']))
                elements.append(Spacer(1, 10))
                
                power_content = self.simulation_results['power_balance']
                if power_content:
                    rows = [[line] for line in power_content.split('\n') if line.strip()]
                    if rows:
                        table = Table(rows, colWidths=[500])
                        table.setStyle(TableStyle([
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        elements.append(table)
    
            # Build PDF
            doc.build(elements)
            
            # Close all buffers after PDF is built
            for buf in buffers:
                buf.close()
            
            messagebox.showinfo("Success", f"Report saved successfully to {file_path}")
    
        except Exception as e:
            # Close buffers even if there's an error
            for buf in buffers:
                buf.close()
            messagebox.showerror("Error", f"Failed to save report: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def clear_results(self):
        """Clear all results and graphs"""
        for text_widget in self.amp_results.values():
            text_widget.delete(1.0, tk.END)
            text_widget.config(state='normal')
        self.power_text.delete(1.0, tk.END)
        self.power_text.config(state='normal')
        self.verify_text.delete(1.0, tk.END)
        self.verify_text.config(state='normal')
    
        # Clear existing graphs
        for frame in self.graph_frames.values():
            for widget in frame.winfo_children():
                widget.destroy()
    
    def disable_text_widgets(self):
        """Disable all text widgets after simulation"""
        for text_widget in self.amp_results.values():
            text_widget.config(state='disabled')
        self.power_text.config(state='disabled')
        self.verify_text.config(state='disabled')

    def create_control_buttons(self):
        button_frame = ttk.Frame(self.main_container)
        button_frame.pack(fill='x', pady=10)

        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side='left', fill='x')

        ttk.Button(left_buttons, text="Save Config As...",
                   command=self.save_config_as).pack(side='left', padx=5)
        ttk.Button(left_buttons, text="Load Configuration",
                   command=self.load_new_configuration).pack(side='left', padx=5)
        ttk.Button(left_buttons, text="Save Changes",
                   command=self.update_config).pack(side='left', padx=5)
        ttk.Button(left_buttons, text="Reset to Original",
                   command=self.reset_config).pack(side='left', padx=5)

    def save_config_as(self):
        if not self.current_config:
            messagebox.showerror("Error", "No configuration loaded")
            return

        try:
            new_file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=Path(self.config_file_path).name if self.config_file_path else "config.json"
            )

            if new_file_path:
                with open(new_file_path, 'w') as file:
                    json.dump(self.current_config, file, indent=4)

                self.config_file_path = new_file_path
                self.update_file_label()

                self.original_config = copy.deepcopy(self.current_config)

                from update_config import update_config
                for amp_num in range(1, self.num_amps + 1):
                    amp_name = f"AMP{amp_num}"
                    updated_config = update_config(self.config_file_path, amp_name)

                    with open(self.config_file_path, 'r') as file:
                        self.current_config = json.load(file)

                    self.update_amplifier_display(amp_name)

                messagebox.showinfo("Success", f"Configuration saved as {Path(new_file_path).name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            import traceback
            traceback.print_exc()

    def load_new_configuration(self):
        if messagebox.askyesno("Load New Configuration",
                               "Loading a new configuration will close the current one. Continue?"):
            for widget in self.main_container.winfo_children():
                widget.destroy()

            self.original_config = None
            self.current_config = None
            self.config_file_path = None
            self.notebook = None
            self.tabs = {}
            self.entry_fields = {}

            self.create_welcome_screen()

    def create_bilan_puissance_tab(self):
        """Create the BILAN_PUISSANCE tab with enhanced layout"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="BILAN_PUISSANCE")
        self.entry_fields['BILAN_PUISSANCE'] = {}

        # Create main container with padding
        main_container = ttk.Frame(tab, padding=20)
        main_container.pack(fill='both', expand=True)

        # Add title
        title_label = ttk.Label(
            main_container,
            text="POWER BALANCE",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # Create frame for parameters
        params_frame = ttk.LabelFrame(main_container, padding=10)
        params_frame.pack(fill='x', expand=True)

        # Define units for parameters
        units = {
            "ATTENUATEUR_PER_PRIN": "%",
            "ATTENUATEUR_PER_AUTRE": "%",
            "COMPRESSEUR_PER_PRIN": "%",
            "COMPRESSEUR_PER_AUTRE": "%",
            "PUISSANCE": "W",
            "OBJECTIF": "TW"
        }

        # Convert decimal values to percentages for display
        display_multiplier = {
            "ATTENUATEUR_PER_PRIN": 100,
            "ATTENUATEUR_PER_AUTRE": 100,
            "COMPRESSEUR_PER_PRIN": 100,
            "COMPRESSEUR_PER_AUTRE": 100,
            "PUISSANCE": 1,
            "OBJECTIF": 1
        }

        # Parameter descriptions
        descriptions = {
            "ATTENUATEUR_PER_PRIN": "Main Attenuator Losses",
            "ATTENUATEUR_PER_AUTRE": "Other Attenuator Losses",
            "COMPRESSEUR_PER_PRIN": "Main Compressor Losses",
            "COMPRESSEUR_PER_AUTRE": "Other Compressor Losses",
            "PUISSANCE": "Power",
            "OBJECTIF": "Target Power"
        }

        # Grid configuration
        params_frame.columnconfigure(1, weight=1)
        
        row = 0
        bilan_data = {k: v for k, v in self.current_config['BILAN_PUISSANCE'].items()
                      if k != 'PUISSANCE'}

        for param_name, param_value in bilan_data.items():
            # Create container frame for each parameter
            param_frame = ttk.Frame(params_frame)
            param_frame.grid(row=row, column=0, columnspan=3, sticky='ew', pady=5)

            # Parameter name with description
            name_label = ttk.Label(
                param_frame, 
                text=descriptions.get(param_name, param_name),
                font=('Arial', 10, 'bold')
            )
            name_label.grid(row=0, column=0, sticky='w', padx=(5, 10))

            # Entry field
            entry = ttk.Entry(param_frame, width=15)
            # Convert value to percentage if needed
            display_value = param_value * display_multiplier.get(param_name, 1)
            entry.insert(0, str(display_value))
            entry.grid(row=0, column=1, padx=5)

            # Unit label
            if param_name in units:
                unit_label = ttk.Label(param_frame, text=units[param_name])
                unit_label.grid(row=0, column=2, padx=(5, 20))

            self.entry_fields['BILAN_PUISSANCE'][param_name] = entry
            row += 1

            # Add tooltip
            tooltip_text = f"Parameter: {descriptions.get(param_name, param_name)}"
            self.create_tooltip(name_label, tooltip_text)

    def update_config(self):
        if not self.config_file_path:
            messagebox.showerror("Error", "No configuration file loaded")
            return

        try:
            for amp_num in range(1, self.num_amps + 1):
                amp_name = f"AMP{amp_num}"
                for section_name, section_fields in self.entry_fields[amp_name].items():
                    for param_name, widget in section_fields.items():
                        # Get value based on widget type
                        if isinstance(widget, ttk.Entry):
                            value = widget.get()
                        else:  # Label
                            value = widget.cget('text')

                        # Convert value to appropriate type
                        try:
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            if value.lower() in ['true', 'false']:
                                value = value.lower() == 'true'
                            elif 'e' in value.lower():
                                try:
                                    value = float(value)
                                except ValueError:
                                    pass

                        self.current_config[amp_name][section_name][param_name] = value

            
            # Special handling for BILAN_PUISSANCE parameters
            percentage_params = [
                "ATTENUATEUR_PER_PRIN",
                "ATTENUATEUR_PER_AUTRE",
                "COMPRESSEUR_PER_PRIN",
                "COMPRESSEUR_PER_AUTRE"
            ]

            for param_name, entry in self.entry_fields['BILAN_PUISSANCE'].items():
                try:
                    value = float(entry.get())
                    # Convert percentages back to decimal
                    if param_name in percentage_params:
                        value = value / 100
                    self.current_config['BILAN_PUISSANCE'][param_name] = value
                except ValueError:
                    pass

            # Handle BILAN_PUISSANCE section
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

            with open(self.config_file_path, 'w') as file:
                json.dump(self.current_config, file, indent=4)

            from update_config import update_config
            for amp_num in range(1, self.num_amps + 1):
                amp_name = f"AMP{amp_num}"
                updated_config = update_config(self.config_file_path, amp_name)

                with open(self.config_file_path, 'r') as file:
                    self.current_config = json.load(file)

                self.update_amplifier_display(amp_name)

            messagebox.showinfo("Success", "Configuration saved and updated successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update configuration: {str(e)}")
            raise

    def update_amplifier_display(self, amp_name):
        for section_name, section_fields in self.entry_fields[amp_name].items():
            for param_name, widget in section_fields.items():
                new_value = self.current_config[amp_name][section_name][param_name]

                if isinstance(widget, ttk.Entry):
                    widget.delete(0, tk.END)
                    widget.insert(0, str(new_value))
                    original_bg = widget.cget('background')
                    widget.configure(background='lightgreen')
                    self.root.after(500, lambda w=widget, bg=original_bg: w.configure(background=bg))
                else:
                    widget.configure(text=str(new_value))

    def reset_config(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all values to original?"):
            self.current_config = copy.deepcopy(self.original_config)

            for amp_num in range(1, self.num_amps + 1):
                amp_name = f"AMP{amp_num}"
                for section_name, section_fields in self.entry_fields[amp_name].items():
                    for param_name, entry in section_fields.items():
                        entry.delete(0, tk.END)
                        entry.insert(0, str(self.original_config[amp_name][section_name][param_name]))

            for param_name, entry in self.entry_fields['BILAN_PUISSANCE'].items():
                entry.delete(0, tk.END)
                entry.insert(0, str(self.original_config['BILAN_PUISSANCE'][param_name]))

    


def SimuAMPGUI():
    root = tk.Tk()
    app = JSONConfigEditor(root)
    root.mainloop()
