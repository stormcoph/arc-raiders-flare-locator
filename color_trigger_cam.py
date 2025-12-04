import dxcam
import cv2
import time
import numpy as np
import tkinter as tk
from tkinter import simpledialog
import keyboard
import math

def main():
    # Initialize DXCam
    camera = dxcam.create(output_color="BGR")
    
    # Target pixel coordinates (x, y)
    TRIGGER_X = 1250
    TRIGGER_Y = 520
    
    # Target color in RGB (E65A4D) -> (230, 90, 77)
    TARGET_COLOR_BGR = (77, 90, 230)
    
    # Region to record (Left, Top, Right, Bottom)
    REGION = (938, 324, 1589, 1009)
    
    # Variable to store the input value and calculated radius
    input_value = None
    calculated_radius = None
    
    def get_input_value():
        nonlocal input_value, calculated_radius
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        value = simpledialog.askinteger("Input", "Enter an integer value:", parent=root)
        root.destroy()
        
        if value is not None:
            input_value = value
            # Calculate radius using formula: (√(input^2 - 350^2)) / 2.07
            try:
                calculated_radius = math.sqrt(value**2 - 350**2) / 2.07
                print(f"Input value: {input_value}, Calculated radius: {calculated_radius:.2f} px")
            except ValueError:
                print(f"Invalid input: {value}^2 must be greater than 350^2 (value must be > 350)")
                input_value = None
                calculated_radius = None
    
    # Set up F7 key listener
    keyboard.on_press_key("f7", lambda _: get_input_value())
    
    print(f"Monitoring pixel ({TRIGGER_X}, {TRIGGER_Y}) for color {TARGET_COLOR_BGR} (BGR)...")
    print("Press F7 to enter a value for circle radius calculation.")
    print("Press 'q' in the projector window to quit.")

    # Start capturing
    camera.start(target_fps=60, video_mode=True)
    
    # Create the window once
    cv2.namedWindow("Projector")

    try:
        while True:
            # Grab the latest frame from the camera buffer
            frame = camera.get_latest_frame()
            
            if frame is None:
                continue
                
            # Check pixel color
            try:
                pixel_color = frame[TRIGGER_Y, TRIGGER_X]
            except IndexError:
                print("Trigger coordinates out of bounds!")
                break

            # Compare color
            if np.array_equal(pixel_color, TARGET_COLOR_BGR):
                # Crop the region
                region_frame = frame[REGION[1]:REGION[3], REGION[0]:REGION[2]].copy()
                
                # --- Icon Detection Start ---
                icon_color_bgr = np.array([232, 200, 84], dtype=np.uint8)
                
                tolerance = 10
                lower_bound = np.clip(icon_color_bgr - tolerance, 0, 255)
                upper_bound = np.clip(icon_color_bgr + tolerance, 0, 255)
                
                mask = cv2.inRange(region_frame, lower_bound, upper_bound)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                valid_rects = []
                direction_fragments = []

                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Precision filter: Disregard icon with width exactly 22 pixels
                    if w == 22:
                        continue
                    
                    # Ignore very small noise (<= 2x2)
                    if w <= 2 or h <= 2:
                        continue
                        
                    # Check for direction fragments (> 2x2 and < 7x7)
                    if w < 7 and h < 7:
                        direction_fragments.append((x, y, w, h))
                    else:
                        # Valid icon
                        valid_rects.append((x, y, w, h))

                # Draw results for valid rects and their direction indicators
                for x, y, w, h in valid_rects:
                    # Draw red box
                    cv2.rectangle(region_frame, (x, y), (x + w, y + h), (0, 0, 255), 1)
                    
                    # Calculate icon center
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    if 0 <= center_x < region_frame.shape[1] and 0 <= center_y < region_frame.shape[0]:
                        # Draw red pixel in the middle
                        region_frame[center_y, center_x] = [0, 0, 255]
                        
                        # Calculate screen coordinates
                        screen_x = REGION[0] + center_x
                        screen_y = REGION[1] + center_y
                        
                        # Draw coordinates text
                        text = f"({screen_x - 938}, {screen_y-324})"
                        cv2.putText(region_frame, text, (center_x + 20, center_y + 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                        
                        # Find closest direction fragment for this icon
                        if direction_fragments:
                            closest_fragment = None
                            min_dist_sq = float('inf')
                            
                            for fx, fy, fw, fh in direction_fragments:
                                fcx = fx + fw // 2
                                fcy = fy + fh // 2
                                dist_sq = (fcx - center_x)**2 + (fcy - center_y)**2
                                
                                if dist_sq < min_dist_sq:
                                    min_dist_sq = dist_sq
                                    closest_fragment = (fx, fy, fw, fh)
                            
                            # Draw line from fragment center extending to circle edge
                            if closest_fragment and calculated_radius is not None:
                                fx, fy, fw, fh = closest_fragment
                                fragment_cx = fx + fw // 2
                                fragment_cy = fy + fh // 2
                                
                                # Calculate direction vector from center to fragment
                                dx = fragment_cx - center_x
                                dy = fragment_cy - center_y
                                
                                # Calculate distance
                                distance = math.sqrt(dx**2 + dy**2)
                                
                                if distance > 0:
                                    # Normalize direction
                                    dx_norm = dx / distance
                                    dy_norm = dy / distance
                                    
                                    # Calculate end point at circle radius
                                    radius_px = int(calculated_radius)
                                    end_x = int(center_x + dx_norm * radius_px)
                                    end_y = int(center_y + dy_norm * radius_px)
                                    
                                    # Draw line from fragment center to circle edge (cyan color)
                                    cv2.line(region_frame, (fragment_cx, fragment_cy), 
                                            (end_x, end_y), (255, 255, 0), 2)
                        
                        # Draw circles if radius is calculated
                        if calculated_radius is not None:
                            radius_px = int(calculated_radius)
                            inner_radius = max(1, radius_px - 15)  # 15px inward
                            outer_radius = radius_px + 15  # 15px outward
                            
                            # Create a mask for the ring (annulus)
                            ring_mask = np.zeros(region_frame.shape[:2], dtype=np.uint8)
                            
                            # Draw outer circle filled
                            cv2.circle(ring_mask, (center_x, center_y), outer_radius, 255, -1)
                            # Subtract inner ring boundary to create ring
                            cv2.circle(ring_mask, (center_x, center_y), inner_radius, 0, -1)
                            
                            # Create red overlay
                            overlay = region_frame.copy()
                            overlay[ring_mask == 255] = [0, 0, 255]
                            
                            # Blend with 30% opacity for the ring only
                            cv2.addWeighted(overlay, 0.3, region_frame, 0.7, 0, region_frame)
                            
                            # Draw inner red circle on top (2px width, solid)
                            cv2.circle(region_frame, (center_x, center_y), radius_px, (0, 0, 255), 2)
                
                # --- Icon Detection End ---

                # Show the frame
                cv2.imshow("Projector", region_frame)
            else:
                time.sleep(0.01)

            # Always process window events
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        keyboard.unhook_all()
        camera.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()