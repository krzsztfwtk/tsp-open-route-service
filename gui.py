import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import yaml
import subprocess
import os
import webbrowser

python_interpreter = "python3"

def str_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(str, str_presenter)

temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)

locations = []
required_stops_vars = {}
required_stops_checkboxes = []
weights = {"distance_km": 0.5, "duration_min": 0.5}

def load_locations():
    global locations
    locations_path = os.path.join(temp_dir, "locations.yaml")
    if os.path.exists(locations_path):
        with open(locations_path, "r") as file:
            data = yaml.safe_load(file)
            locations = data.get("locations", [])
        update_location_options()

def add_location():
    name = simpledialog.askstring("Location Name", "Enter the name of the location:")
    if not name:
        return
    coordinates = simpledialog.askstring("Coordinates", "Enter coordinates (latitude, longitude):")
    if not coordinates:
        return
    try:
        lat, lon = map(float, coordinates.split(","))
    except (ValueError, TypeError):
        messagebox.showerror("Error", "Invalid format. Enter coordinates as 'latitude, longitude'.")
        return
    locations.append({"name": name, "coords": [lat, lon]})
    update_location_options()

def update_location_options():
    start_location_menu['values'] = [loc["name"] for loc in locations]
    end_location_menu['values'] = [loc["name"] for loc in locations]
    for checkbox in required_stops_checkboxes:
        checkbox.grid_forget()
    required_stops_checkboxes.clear()
    for loc in locations:
        var = tk.BooleanVar()
        checkbox = tk.Checkbutton(required_stops_frame, text=loc["name"], variable=var, command=update_required_stops)
        checkbox.grid(sticky="W")
        required_stops_vars[loc["name"]] = var
        required_stops_checkboxes.append(checkbox)
    update_required_stops()

def update_required_stops():
    selected_start = start_location_menu.get()
    selected_end = end_location_menu.get()
    for name, var in required_stops_vars.items():
        var.set(var.get() and name != selected_start and name != selected_end)
        if name == selected_start or name == selected_end:
            var.set(False)
            required_stops_vars[name].set(False)
            required_stops_checkboxes[locations.index(next(loc for loc in locations if loc["name"] == name))].config(state="disabled")
        else:
            required_stops_checkboxes[locations.index(next(loc for loc in locations if loc["name"] == name))].config(state="normal")

def set_weights():
    distance_weight = simpledialog.askfloat("Distance Weight", "Enter weight for distance (0-1):", minvalue=0, maxvalue=1)
    duration_weight = simpledialog.askfloat("Duration Weight", "Enter weight for duration (0-1):", minvalue=0, maxvalue=1)
    if distance_weight + duration_weight == 1:
        global weights
        weights = {"distance_km": distance_weight, "duration_min": duration_weight}
    else:
        messagebox.showerror("Error", "The weights must sum up to 1.")

def save_configurations():
    start_location = start_location_menu.get()
    end_location = end_location_menu.get()
    required_stops = [name for name, var in required_stops_vars.items() if var.get()]
    with open(os.path.join(temp_dir, "locations.yaml"), "w") as file:
        yaml.dump({"locations": locations}, file, Dumper=yaml.SafeDumper)
    config_data = {
        "start_location": start_location,
        "end_location": end_location,
        "required_stops": required_stops,
        "weights": weights
    }
    with open(os.path.join(temp_dir, "config.yaml"), "w") as file:
        yaml.dump(config_data, file, default_flow_style=None, allow_unicode=True, Dumper=yaml.SafeDumper)

def generate_files_and_calculate_route():
    save_configurations()
    
    distances_file = os.path.join(temp_dir, "distances.yaml")
    
    # Check if the distances file already exists
    if os.path.exists(distances_file):
        # Run generate_distances.py with the existing distances file as input for -d
        subprocess.run([
            python_interpreter, "generate_distances.py", 
            "-i", os.path.join(temp_dir, "locations.yaml"), 
            "-d", distances_file, 
            "-o", distances_file  # Overwrite or update the existing distances file
        ])
    else:
        # Run generate_distances.py without -d if distances file doesn't exist
        subprocess.run([
            python_interpreter, "generate_distances.py", 
            "-i", os.path.join(temp_dir, "locations.yaml"), 
            "-o", distances_file
        ])
    
    # Run find_route.py with the distances and config files
    subprocess.run([
        python_interpreter, "find_route.py", 
        "-d", distances_file, 
        "-c", os.path.join(temp_dir, "config.yaml"), 
        "-o", os.path.join(temp_dir, "route_output.yaml")
    ])
def draw_map():
    subprocess.run([python_interpreter, "draw_route_on_map.py", "-l", os.path.join(temp_dir, "locations.yaml"), "-r", os.path.join(temp_dir, "route_output.yaml"), "-o", os.path.join(temp_dir, "map.html")])
    webbrowser.open(os.path.join(temp_dir, "map.html"))

root = tk.Tk()
root.title("TSP Route Planner GUI")

tk.Label(root, text="TSP Route Planner", font=("Helvetica", 16)).grid(row=0, column=0, columnspan=3, pady=10)

tk.Button(root, text="Add Location", command=add_location, width=20).grid(row=1, column=0, padx=5, pady=5)
tk.Button(root, text="Set Weights", command=set_weights, width=20).grid(row=2, column=0, padx=5, pady=5)

tk.Label(root, text="Start Location:").grid(row=3, column=0, padx=5, pady=5, sticky="E")
start_location_menu = ttk.Combobox(root, state="readonly")
start_location_menu.grid(row=3, column=1, padx=5, pady=5, sticky="W")
start_location_menu.bind("<<ComboboxSelected>>", lambda _: update_required_stops())

tk.Label(root, text="End Location:").grid(row=4, column=0, padx=5, pady=5, sticky="E")
end_location_menu = ttk.Combobox(root, state="readonly")
end_location_menu.grid(row=4, column=1, padx=5, pady=5, sticky="W")
end_location_menu.bind("<<ComboboxSelected>>", lambda _: update_required_stops())

required_stops_frame = tk.Frame(root)
required_stops_frame.grid(row=5, column=1, sticky="W", padx=5, pady=5)
tk.Label(root, text="Required Stops (exclude start/end):").grid(row=5, column=0, padx=5, pady=5, sticky="NE")

tk.Button(root, text="Generate & Calculate Route", command=generate_files_and_calculate_route, width=30).grid(row=6, column=0, columnspan=3, padx=5, pady=10)
tk.Button(root, text="Draw & Open Map", command=draw_map, width=30).grid(row=7, column=0, columnspan=3, padx=5, pady=10)

load_locations()
root.mainloop()
