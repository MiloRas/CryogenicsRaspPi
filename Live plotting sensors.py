import sys # Provides access to system-specific parameters and functions
import time # Provides time-related functions
from daqhats import hat_list, HatIDs, mcc172, OptionFlags # device access and config
import numpy as np # For numerical operations (e.g., averaging)
import matplotlib.pyplot as plt # For plotting graphs
from matplotlib.animation import FuncAnimation # For real-time plot updates
from collections import deque # Provides a fast and memory-efficient queue


board_list = hat_list(filter_by_id=HatIDs.MCC_172) # Lists MCC 172 boards and filter by ID

if not board_list:          # If no MCC 172 is detected, exit the script
    print("No boards found")
    sys.exit()
    
address = board_list[0].address # Get the address of the first detected MCC 172 board
board = mcc172(address) # Initialize the board object

board.a_in_scan_stop() # Ensure any previous scans are stopped and cleaned up
board.a_in_scan_cleanup()

for ch in [0,1]:  # Disable IEPE (excitation) on channel 0 and 1
    board.iepe_config_write(ch, False)

sample_rate = 100 # Sampling rate in Hz
board.a_in_clock_config_write(0, sample_rate) # Config clock and sample rate on board

channel_mask = (1 << 0) | (1 << 1) # Enable ch 0 and 1 by setting their bits in the mask
samples_per_channel = 25 # Number of samples to read per channel in each scan
options = OptionFlags.CONTINUOUS # Set scan to continuous mode so it keeps collecting data
board.a_in_scan_start(channel_mask, samples_per_channel, options) # Start analog input scan


window_size = 300 # Display window in seconds
# Buffer for time values
time_buffer = deque([], maxlen=window_size * sample_rate // samples_per_channel)
# Buffer for voltage values
voltage_buffer = deque([], maxlen=window_size * sample_rate // samples_per_channel)

# Set up the plot for live updating
fig, ax = plt.subplots() # Create figure and axes for plot
line, = ax.plot([],[], color='blue', label='Voltage') # Create an empty line object
ax.set_ylim(-0.01, 0.01) # Set y-axis limits for voltage
ax.set_title("Live Voltage Output from MFC Sensor(MCC 172)") # title of the plot
ax.set_xlabel("Time in Sec") # x axis label
ax.set_ylabel("Voltage (V)") # y axis label
ax.legend() # shows the plot legend
ax.grid(True) # Enable grid lines on the plot



start_time = time.time() # Record the starting time for elapsed time calculations
frame_count = 0 # Initialize frame counter
def update(frame): # Define the update function called by the animation loop
    global frame_count
    frame_count += 1
    try:
        # Read 'samples_per_channel' samples from both channels (0 and 1)
        result = board.a_in_scan_read_numpy(samples_per_channel, timeout=0)
        if result.data.size > 0: # Only proceed if data was returned
            voltage = np.mean(result.data) # Compute avg volt from all returned samples
            current_time = time.time() - start_time  # Calc the elapsed time since start
            voltage_buffer.append(voltage) # Append the voltage reading to the buffer
            time_buffer.append(current_time) # Append the time value to the buffer
            line.set_data(time_buffer, voltage_buffer) # Update the line with new data
            ax.set_xlim(max(0, current_time - window_size), current_time)  # Update x-axis to slide frwd
        else:
            print("No data returned.") # Inform user if no data was collected        
    except Exception as e:
        print(f"Error reading data: {e}") # Catch and report any read errors
    return [line] # Return updated line object for animation

# Start the animation: call `update` every 50 ms
ani = FuncAnimation(fig, update, interval=50, blit=False) 
plt.tight_layout() # Adjust layout to fit plot elements cleanly
plt.show() # Display the animated plot

board.a_in_scan_stop() # After the plot window is closed, stop and clean up the scan
board.a_in_scan_cleanup()

