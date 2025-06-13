import sys
import time
# Import MCC DAQ HAT libraries
from daqhats import hat_list, HatIDs, mcc172, OptionFlags
# Import data handling and plotting libraries
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# List available MCC 172 boards and filter by ID
board_list = hat_list(filter_by_id=HatIDs.MCC_172)

# If no MCC 172 is detected, exit the script
if not board_list:
    print("No boards found")
    sys.exit()
    
# Get the address of the first detected MCC 172 board
address = board_list[0].address

# Initialize the board object
board = mcc172(address)

# Ensure any previous scans are stopped and cleaned up
board.a_in_scan_stop()
board.a_in_scan_cleanup()

# Disable IEPE (excitation) on channel 0
for ch in [0,1]:
    board.iepe_config_write(ch, False)

sample_rate = 100 #Hz

board.a_in_clock_config_write(0, sample_rate)

# Set up scan parameters
channel_mask = 1 << 0
samples_per_channel = 25
options = OptionFlags.CONTINUOUS

# Start the scan
board.a_in_scan_start(channel_mask, samples_per_channel, options)

# Set up fixed-length buffers for plotting last 60 seconds of data
window_size = 300
time_buffer = deque([], maxlen=window_size * sample_rate // samples_per_channel)
voltage_buffer = deque([], maxlen=window_size * sample_rate // samples_per_channel)

# Set up the plot
fig, ax = plt.subplots()                                 # Create figure and axis
line, = ax.plot([],[], color='blue', label='Voltage')    # Create an empty line object
#ax.set_xlim(0,60)
ax.set_ylim(-0.01, 0.01)
ax.set_title("Live Voltage Output from MFC Sensor(MCC 172)")
ax.set_xlabel("Time in Sec")
ax.set_ylabel("Voltage (V)")
ax.legend()
ax.grid(True)

#board.a_in_sensitivity_write(ch, 0.1)  # 0.1 V/unit  #####

start_time = time.time()

frame_count = 0

def update(frame):
    global frame_count
    frame_count += 1
    #print("Update frame:", frame_count)
    try:
        result = board.a_in_scan_read_numpy(samples_per_channel, timeout=0)
        if result.data.size > 0:
            voltage = np.mean(result.data)
            current_time = time.time() - start_time  # <-- REAL time
            voltage_buffer.append(voltage)
            time_buffer.append(current_time)
            #print("Frame:", frame_count, "Shape:", result.data.shape)
            
            line.set_data(time_buffer, voltage_buffer)
            ax.set_xlim(max(0, current_time - window_size), current_time)
            
            #print("Time buffer:", list(time_buffer))
            #print("Voltage buffer:", list(voltage_buffer))
            #print("Result shape:", result.data.shape)
            #print(f"Voltage at {time.strftime('%H:%M:%S')}: {voltage:.6f} V")
        else:
            print("No data returned.")
        
    except Exception as e:
        print(f"Error reading data: {e}")
    return [line]

ani = FuncAnimation(fig, update, interval=50, blit=False)
plt.tight_layout()
plt.show()


   
    
board.a_in_scan_stop()
board.a_in_scan_cleanup()

