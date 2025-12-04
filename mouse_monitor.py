import ctypes
import time
import sys

# Define the POINT structure for GetCursorPos
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_cursor_pos():
    """Returns the current (x, y) position of the cursor."""
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def main():
    print("Monitoring mouse position... (Press Ctrl+C to stop)")
    
    try:
        # Initialize state
        last_x, last_y = get_cursor_pos()
        last_move_time = time.time()
        printed_for_stop = False
        
        while True:
            current_x, current_y = get_cursor_pos()
            current_time = time.time()
            
            # Check if mouse has moved
            if current_x != last_x or current_y != last_y:
                last_move_time = current_time
                last_x, last_y = current_x, current_y
                printed_for_stop = False
            else:
                # Mouse hasn't moved
                # Check if it has been idle for at least 500ms (0.5 seconds)
                if not printed_for_stop and (current_time - last_move_time >= 0.5):
                    print(f"Mouse stopped at: ({current_x}, {current_y})")
                    printed_for_stop = True
            
            # Small sleep to prevent high CPU usage
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()


#1259 ; 1009 = 0 meter distance

# LEFT: 969 ; 1009 = 592m
# RIGHT: 1589 ; 1009 = 698m
# Total = 1290m