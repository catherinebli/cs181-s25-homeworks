# this is a popup that will record data

import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import csv

class VideoCoordinateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Frame Coordinate Extractor")
        
        # Video handling variables
        self.frames = []
        self.current_frame_idx = 0
        self.coordinates = {}  # Format: {frame_idx: {object_name: [(x,y), ...]}}
        
        # Object tracking variables
        self.objects = []
        self.current_object = None
        
        # Add crosshair variables
        self.crosshair_size = 10
        self.crosshair_id = None
        
        # First show object setup
        self.setup_object_window()
        
    def setup_object_window(self):
        # Clear main window first
        for widget in self.root.winfo_children():
            widget.destroy()
            
        setup_frame = ttk.Frame(self.root)
        setup_frame.pack(pady=20, padx=20)
        
        ttk.Label(setup_frame, text="Enter number of objects:").pack()
        self.num_objects_var = tk.StringVar()
        num_entry = ttk.Entry(setup_frame, textvariable=self.num_objects_var)
        num_entry.pack(pady=5)
        
        ttk.Button(setup_frame, text="Next", command=self.get_object_names).pack(pady=10)
        
    def get_object_names(self):
        try:
            num_objects = int(self.num_objects_var.get())
        except ValueError:
            return
            
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        name_frame = ttk.Frame(self.root)
        name_frame.pack(pady=20, padx=20)
        
        ttk.Label(name_frame, text="Enter object names:").pack()
        self.name_entries = []
        
        for i in range(num_objects):
            entry = ttk.Entry(name_frame)
            entry.pack(pady=2)
            self.name_entries.append(entry)
            
        ttk.Button(name_frame, text="Start", command=self.start_main_app).pack(pady=10)
        
    def start_main_app(self):
        # Get object names and keep track of empty entries
        self.objects = []
        for entry in self.name_entries:
            name = entry.get().strip()
            if name:  # If name is not empty
                self.objects.append(name)
            else:  # If name is empty, use "Object_N" as placeholder
                self.objects.append(f"Object_{len(self.objects) + 1}")
            
        if not self.objects:
            return
        
        # Clear window and create main interface
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.create_widgets()
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.get_coordinates)
        self.canvas.bind('<Motion>', self.update_crosshair)
        
    def create_widgets(self):
        # Top controls
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(pady=5)
        
        self.load_btn = ttk.Button(controls_frame, text="Load Video", command=self.load_video)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        # Navigation buttons
        self.prev_btn = ttk.Button(controls_frame, text="Previous Frame", command=self.prev_frame)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = ttk.Button(controls_frame, text="Next Frame", command=self.next_frame)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Frame counter
        self.frame_label = ttk.Label(controls_frame, text="Frame: 0/0")
        self.frame_label.pack(side=tk.LEFT, padx=5)
        
        # Save button
        self.save_btn = ttk.Button(controls_frame, text="Save Coordinates", command=self.save_coordinates)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Add undo button
        self.undo_btn = ttk.Button(controls_frame, text="Undo Last Click", command=self.undo_last_click)
        self.undo_btn.pack(side=tk.LEFT, padx=5)
        
        # Object selection frame
        object_frame = ttk.LabelFrame(self.root, text="Select Object")
        object_frame.pack(pady=5, fill="x", padx=5)
        
        # Create radio buttons for each object
        self.object_var = tk.StringVar(value=self.objects[0])
        for obj in self.objects:
            ttk.Radiobutton(object_frame, text=obj, value=obj, 
                           variable=self.object_var).pack(side=tk.LEFT, padx=5)
        
        # Canvas for displaying frames
        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack(pady=5)
        
        # Coordinates display
        self.coord_label = ttk.Label(self.root, text="Click on the image to get coordinates")
        self.coord_label.pack(pady=5)

    def load_video(self):
        from tkinter import filedialog
        video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi")])
        if not video_path:
            return
            
        # Clear previous frames
        self.frames = []
        self.coordinates = {}
        
        # Extract frames
        cap = cv2.VideoCapture(video_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frames.append(frame)
        cap.release()
        
        self.current_frame_idx = 0
        self.show_current_frame()
        
    def show_current_frame(self):
        if not self.frames:
            return
            
        frame = self.frames[self.current_frame_idx]
        # Resize frame to fit canvas while maintaining aspect ratio
        height, width = frame.shape[:2]
        scale = min(800/width, 600/height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        frame = cv2.resize(frame, (new_width, new_height))
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Redraw all stored coordinates for this frame
        if self.current_frame_idx in self.coordinates:
            frame_data = self.coordinates[self.current_frame_idx]
            for obj_name, coords_list in frame_data.items():
                color = self.get_color_for_object(obj_name)
                for x, y in coords_list:
                    # Draw point
                    self.canvas.create_oval(
                        x - 2, y - 2, x + 2, y + 2,
                        fill=color,
                        outline=color
                    )
                    # Draw label
                    self.canvas.create_text(x + 10, y + 10, text=obj_name, fill=color)
        
        # Update frame counter
        self.frame_label.config(text=f"Frame: {self.current_frame_idx + 1}/{len(self.frames)}")
        
        # Show stored coordinates for this frame
        if self.current_frame_idx in self.coordinates:
            coords = self.coordinates[self.current_frame_idx]
            self.coord_label.config(text=f"Stored coordinates for frame {self.current_frame_idx + 1}: {coords}")
        else:
            self.coord_label.config(text="Click on the image to get coordinates")
    
    def update_crosshair(self, event):
        # Remove previous crosshair
        if self.crosshair_id:
            for id in self.crosshair_id:
                self.canvas.delete(id)
        
        # Draw new crosshair
        x, y = event.x, event.y
        size = self.crosshair_size
        self.crosshair_id = [
            self.canvas.create_line(x - size, y, x + size, y, fill='red'),
            self.canvas.create_line(x, y - size, x, y + size, fill='red')
        ]
    
    def save_coordinates(self):
        if not self.frames:  # Make sure we have frames to save
            return
        
        # Create directory for saving
        save_dir = filedialog.askdirectory(title="Select Directory to Save")
        if not save_dir:
            return
        
        # Create subdirectories
        frames_dir = os.path.join(save_dir, 'frames')
        labeled_frames_dir = os.path.join(save_dir, 'labeled_frames')
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(labeled_frames_dir, exist_ok=True)
        
        # Save CSV file
        csv_path = os.path.join(save_dir, 'coordinates.csv')
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Frame', 'Object', 'X', 'Y'])  # Header
            
            # Get the number of objects from initial setup
            num_objects = len(self.name_entries)
            
            # Save frames and coordinates
            for frame_idx in range(len(self.frames)):
                frame = self.frames[frame_idx]
                orig_height, orig_width = frame.shape[:2]
                
                # Calculate scale factors
                canvas_scale = min(800/orig_width, 600/orig_height)
                canvas_width = int(orig_width * canvas_scale)
                canvas_height = int(orig_height * canvas_scale)
                
                # Scale factors to convert canvas coordinates back to original image coordinates
                scale_x = orig_width / canvas_width
                scale_y = orig_height / canvas_height
                
                # Save original frame
                frame_path = os.path.join(frames_dir, f'frame_{frame_idx+1}.jpg')
                cv2.imwrite(frame_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                
                # Create labeled frame
                labeled_frame = frame.copy()
                if frame_idx in self.coordinates:
                    frame_data = self.coordinates[frame_idx]
                    for obj_name, coords_list in frame_data.items():
                        color = self.get_color_for_object(obj_name)
                        bgr_color = self.name_to_bgr_color(color)
                        for canvas_x, canvas_y in coords_list:
                            # Convert canvas coordinates to original image coordinates
                            orig_x = int(canvas_x * scale_x)
                            orig_y = int(canvas_y * scale_y)
                            
                            # Draw point and label on the frame
                            cv2.circle(labeled_frame, (orig_x, orig_y), 5, bgr_color, -1)
                            cv2.putText(labeled_frame, obj_name, 
                                      (orig_x + 10, orig_y + 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 1, bgr_color, 2)
                
                # Save labeled frame
                labeled_path = os.path.join(labeled_frames_dir, f'frame_{frame_idx+1}.jpg')
                cv2.imwrite(labeled_path, cv2.cvtColor(labeled_frame, cv2.COLOR_RGB2BGR))
                
                # Write coordinates to CSV (using original coordinates)
                if frame_idx in self.coordinates:
                    frame_data = self.coordinates[frame_idx]
                    for i in range(num_objects):
                        obj_name = self.objects[i] if i < len(self.objects) else f"Object_{i+1}"
                        if obj_name in frame_data and frame_data[obj_name]:
                            for canvas_x, canvas_y in frame_data[obj_name]:
                                orig_x = int(canvas_x * scale_x)
                                orig_y = int(canvas_y * scale_y)
                                writer.writerow([frame_idx + 1, obj_name, orig_x, orig_y])
                        else:
                            writer.writerow([frame_idx + 1, obj_name, 'NaN', 'NaN'])
                else:
                    for i in range(num_objects):
                        obj_name = self.objects[i] if i < len(self.objects) else f"Object_{i+1}"
                        writer.writerow([frame_idx + 1, obj_name, 'NaN', 'NaN'])
        
        self.coord_label.config(text=f"Data saved to {save_dir}")
    
    def name_to_bgr_color(self, color_name):
        # Convert color names to BGR values
        color_dict = {
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'green': (0, 255, 0),
            'purple': (255, 0, 255),
            'orange': (0, 165, 255),
            'brown': (42, 42, 165),
            'pink': (203, 192, 255)
        }
        return color_dict.get(color_name, (0, 0, 255))  # Default to red if color not found
    
    def get_coordinates(self, event):
        if not self.frames:
            return
            
        x, y = event.x, event.y
        current_obj = self.object_var.get()
        
        # Initialize frame in coordinates if needed
        if self.current_frame_idx not in self.coordinates:
            self.coordinates[self.current_frame_idx] = {}
        
        # Initialize object in frame if needed
        if current_obj not in self.coordinates[self.current_frame_idx]:
            self.coordinates[self.current_frame_idx][current_obj] = []
            
        # Add coordinates
        self.coordinates[self.current_frame_idx][current_obj].append((x, y))
        
        # Draw point with object name
        color = self.get_color_for_object(current_obj)
        self.canvas.create_oval(
            x - 2, y - 2, x + 2, y + 2,
            fill=color,
            outline=color
        )
        self.canvas.create_text(x + 10, y + 10, text=current_obj, fill=color)
        
        self.coord_label.config(
            text=f"{current_obj} coordinates: ({x}, {y})"
        )
    
    def get_color_for_object(self, object_name):
        # Generate different colors for different objects
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink']
        return colors[self.objects.index(object_name) % len(colors)]
    
    def next_frame(self):
        if self.frames and self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            self.show_current_frame()
    
    def prev_frame(self):
        if self.frames and self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self.show_current_frame()

    def undo_last_click(self):
        if not self.frames or self.current_frame_idx not in self.coordinates:
            return
        
        current_obj = self.object_var.get()
        frame_data = self.coordinates[self.current_frame_idx]
        
        if current_obj in frame_data and frame_data[current_obj]:
            # Remove last coordinate for current object
            frame_data[current_obj].pop()
            
            # If no more coordinates for this object, remove the object entry
            if not frame_data[current_obj]:
                del frame_data[current_obj]
            
            # If no more objects in frame, remove frame entry
            if not frame_data:
                del self.coordinates[self.current_frame_idx]
            
            # Redraw frame with updated coordinates
            self.show_current_frame()
            
            self.coord_label.config(text="Last coordinate undone")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCoordinateApp(root)
    root.mainloop() 