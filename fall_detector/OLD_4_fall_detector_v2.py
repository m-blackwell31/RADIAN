M. Blackwell
scrubdaddy501
T-36 days until 🎓

AndySalad — 2/19/2026 9:43 AM
Image
Image
AndySalad — 2/19/2026 10:17 AM
Image
AndySalad — 2/19/2026 10:32 AM
Attachment file type: unknown
Base.STEP
320.89 KB
Attachment file type: unknown
Lid.STEP
1.04 MB
AndySalad — 2/19/2026 10:46 AM
LegPrint will need 4
Attachment file type: unknown
LegPrint.STEP
22.63 KB
AndySalad — 2/22/2026 2:33 PM
This zip is our current SRR-based radar ML pipeline progress. recordings_raw/ has raw SRR GUI binary captures, tracks_csv/ has parsed SRR track rows, labeled_csv/ adds clip labels + row trend helpers, and windows/ has sliding-window engineered features for baseline ML. scripts/ contains the parser/label/window generation code. Old/ is archive/debug stuff and mostly not needed. Main caveat: SRR tracker output can be noisy/jumpy, so treat this as baseline data/pipeline validation rather than final-quality dataset.
Attachment file type: archive
Progress.zip
745.05 KB
chat ahh explanation
AndySalad — 3/25/2026 4:03 PM
Attachment file type: archive
RADIAN_package.zip
2.51 MB
AndySalad — 3/26/2026 7:36 AM
To use it just add "--debug" to the run command:

python3 fall_detector_v2.py \
  --parser mmwave_run6.py \
  --model  best_model_pi_v3.pkl \
  --cli-port /dev/ttyUSB0 \
  --data-port /dev/ttyUSB1 \
  --cfg-file config3.cfg \
  --debug

The dashboard has four panels — point cloud top-down view, Z height over time, velocity over time, and a probability bar with a live FALL/ok badge. Press q to quit, c to clear the history. Without --debug the file adds zero overhead — debug_dashboard.py only gets imported if you explicitly ask for it. 
"""
debug_dashboard.py
==================
Terminal debug dashboard for the RADIAN fall detector.
Uses Python's built-in curses — no extra dependencies.

debug_dashboard.py
19 KB
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

fall_detector_v2.py
28 KB
M. Blackwell — 3/26/2026 7:37 AM
Perfect
This is the second version of the fall detector, can I use the 3rd one? (I may incorrect in thinking that we have the 3rd one)
AndySalad — 3/26/2026 7:37 AM
Just replace the fall_dectector_V2.py and add the debug_dashboard.py
There is a modelV3 and a fall dectorV2 you might be thinking of the model
"best_modelv3" is the ML stuff and "Fall-detectorv2" is the parsing + ML + alert stuff
Also, I don't know if you saw it but there is a gotify section somewhere and we can add our url and token
M. Blackwell — 3/26/2026 7:42 AM
I did see that, I’ll have to add it today, because I forgot what Mitch had it set at
But it works without it, it just throws an warning that nothing is connected
AndySalad — 3/26/2026 8:49 AM
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

fall_detector_v2.py
29 KB
python3 fall_detector_v2.py \
  --parser     mmwave_run6.py \
  --model      best_model_pi_v3.pkl \
  --cli-port   /dev/ttyUSB0 \
  --data-port  /dev/ttyUSB1 \
  --cfg-file   config3.cfg \
  --gotify-url   http://your_server:8080/ \
  --gotify-token YOUR_TOKEN \
  --verbose
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

fall_detector_v2.py
29 KB
AndySalad — 3/26/2026 9:04 AM
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

fall_detector_v2.py
29 KB
AndySalad — 3/26/2026 9:16 AM
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

fall_detector_v2.py
29 KB
AndySalad — 3/26/2026 9:57 AM
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
Add your network at the bottom:

network={
    ssid="YourNetworkName"
    psk="YourPassword"
}
sudo wpa_cli -i wlan0 reconfigure
M. Blackwell — 3/26/2026 10:00 AM
PS C:\Users\matth> hostname -I
sethostname: Use the Network Control Panel Applet to set hostname.
hostname -s is not supported.
PS C:\Users\matth>
AndySalad — 3/30/2026 11:50 AM
scp pi@<PI_IP>:~/fall_detector/fall_log.csv ./
python3 -m http.server 8000
Run that on the Pi, then on your laptop open a browser and go to:

http://<PI_IP>:8000
M. Blackwell — 3/30/2026 11:54 AM
timestamp,prediction,probability,alert_sent
2026-03-25 23:10:24,1,0.4470,1
2026-03-25 23:10:28,1,0.4470,0
2026-03-25 23:10:30,1,0.4470,0
2026-03-25 23:10:33,1,0.4470,0
2026-03-25 23:10:35,1,0.4470,0

fall_log.csv
29 KB
AndySalad — 3/30/2026 11:56 AM
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

fall_detector_v2.py
30 KB
python3 fall_detector_v2.py \
  --parser     mmwave_run6.py \
  --model      best_model_pi_v3.pkl \
  --cli-port   /dev/ttyUSB0 \
  --data-port  /dev/ttyUSB1 \
  --cfg-file   config3.cfg \
  --threshold  0.55 \
  --gotify-url   http://your_server:8080/ \
  --gotify-token YOUR_TOKEN \
  --verbose
python3 mmwave_run6.py | head -20
M. Blackwell — 3/30/2026 12:03 PM
[INFO] Opening ports: CLI=COM5 (115200)  DATA=COM6 (921600)
Traceback (most recent call last):
  File "/home/mblackwell31/RADIAN/RADIAN_env/lib/python3.13/site-packages/serial/serialposix.py", line 322, in open
    self.fd = os.open(self.portstr, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
              ~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'COM5'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/mblackwell31/RADIAN/fall_detector/mmwave_run6.py", line 456, in <module>
    main()
    ^^
  File "/home/mblackwell31/RADIAN/fall_detector/mmwave_run6.py", line 333, in main
    cli, data = open_ports()
                ~~^^
  File "/home/mblackwell31/RADIAN/fall_detector/mmwave_run6.py", line 100, in open_ports
    cli  = serial.Serial(CLI_PORT,  CLI_BAUD,  timeout=TIMEOUT)
  File "/home/mblackwell31/RADIAN/RADIAN_env/lib/python3.13/site-packages/serial/serialutil.py", line 244, in init
    self.open()
    ~~~^^
  File "/home/mblackwell31/RADIAN/RADIAN_env/lib/python3.13/site-packages/serial/serialposix.py", line 325, in open
    raise SerialException(msg.errno, "could not open port {}: {}".format(self._port, msg))
serial.serialutil.SerialException: [Errno 2] could not open port COM5: [Errno 2] No such file or directory: 'COM5'
[INFO] Opening ports: CLI=/dev/ttyUSB0 (115200)  DATA=/dev/ttyUSB1 (921600)
[INFO] Running... (Ctrl+C to stop)
{"ts": 0.288, "frame": 1, "num_points_filt": 3, "points_filt": [{"x": 0.961, "y": 1.552, "z": 0.932, "v": -0.161}, {"x": 0.0, "y": 2.387, "z": 0.236, "v": -0.161}, {"x": 4.463, "y": 2.177, "z": 2.824, "v": -0.04}], "person": {"present": false}}
{"ts": 0.789, "frame": 2, "num_points_filt": 1, "points_filt": [{"x": 0.94, "y": 1.683, "z": 0.554, "v": -0.161}], "person": {"present": false}}
{"ts": 1.291, "frame": 4, "num_points_filt": 4, "points_filt": [{"x": 0.878, "y": 1.755, "z": 0.418, "v": -0.161}, {"x": 1.987, "y": 1.161, "z": 0.5, "v": -0.121}, {"x": 4.216, "y": 1.343, "z": 2.711, "v": -0.121}, {"x": 5.265, "y": 2.834, "z": -0.676, "v": -0.08}], "person": {"present": false}}
{"ts": 1.792, "frame": 6, "num_points_filt": 3, "points_filt": [{"x": 4.347, "y": 2.012, "z": 0.253, "v": 0.201}, {"x": 1.156, "y": 1.165, "z": 1.628, "v": -0.08}, {"x": 1.95, "y": 1.206, "z": 0.291, "v": -0.08}], "person": {"present": false}}

message.txt
5 KB
[INFO] Opening ports: CLI=/dev/ttyUSB0 (115200)  DATA=/dev/ttyUSB1 (921600)
[INFO] Running... (Ctrl+C to stop)
{"ts": 0.284, "frame": 1, "num_points_filt": 14, "points_filt": [{"x": -0.076, "y": 2.347, "z": -0.669, "v": 0.04}, {"x": 0.897, "y": 3.769, "z": -1.338, "v": 0.04}, {"x": 0.0, "y": 2.087, "z": -1.577, "v": 0.08}, {"x": -0.188, "y": 2.436, "z": 1.756, "v": 0.08}, {"x": -0.101, "y": 3.104, "z": 0.874, "v": 0.08}, {"x": 0.174, "y": 2.709, "z": -0.649, "v": 0.121}, {"x": -0.091, "y": 2.918, "z": -0.11, "v": 0.121}, {"x": 2.434, "y": 2.04, "z": 2.591, "v": 0.241}, {"x": 0.897, "y": 3.886, "z": -0.947, "v": 0.241}, {"x": 0.083, "y": 2.48, "z": -0.958, "v": 0.362}, {"x": -0.08, "y": 2.543, "z": -0.383, "v": -0.04}, {"x": -0.086, "y": 2.725, "z": 0.339, "v": -0.04}, {"x": 0.098, "y": 3.112, "z": 0.407, "v": -0.04}, {"x": 2.281, "y": 2.597, "z": 2.121, "v": -0.04}], "person": {"present": true, "confidence": 0.4, "center": {"x": -0.078, "y": 2.717, "z": -0.246, "v": 0.06}, "num_points": 8, "points": [{"x": -0.08, "y": 2.543, "z": -0.383, "v": -0.04}, {"x": -0.091, "y": 2.918, "z": -0.11, "v": 0.121}, {"x": 0.174, "y": 2.709, "z": -0.649, "v": 0.121}, {"x": -0.076, "y": 2.347, "z": -0.669, "v": 0.04}, {"x": -0.086, "y": 2.725, "z": 0.339, "v": -0.04}, {"x": 0.083, "y": 2.48, "z": -0.958, "v": 0.362}, {"x": 0.098, "y": 3.112, "z": 0.407, "v": -0.04}, {"x": -0.101, "y": 3.104, "z": 0.874, "v": 0.08}]}}
{"ts": 0.682, "frame": 2, "num_points_filt": 8, "points_filt": [{"x": -0.153, "y": 2.421, "z": -0.28, "v": 0.04}, {"x": 0.0, "y": 3.224, "z": -0.138, "v": 0.04}, {"x": 0.083, "y": 2.554, "z": -0.739, "v": 0.08}, {"x": 0.191, "y": 3.037, "z": -0.235, "v": 0.08}, {"x": 0.089, "y": 2.708, "z": -0.833, "v": 0.121}, {"x": -0.161, "y": 2.564, "z": -0.142, "v": -0.04}, {"x": 0.0, "y": 3.045, "z": 0.562, "v": -0.04}, {"x": 2.306, "y": 2.239, "z": 2.544, "v": -0.04}], "person": {"present": true, "confidence": 0.399, "center": {"x": 0.042, "y": 2.636, "z": -0.258, "v": 0.06}, "num_points": 6, "points": [{"x": -0.161, "y": 2.564, "z": -0.142, "v": -0.04}, {"x": -0.153, "y": 2.421, "z": -0.28, "v": 0.04}, {"x": 0.191, "y": 3.037, "z": -0.235, "v": 0.08}, {"x": 0.083, "y": 2.554, "z": -0.739, "v": 0.08}, {"x": 0.089, "y": 2.708, "z": -0.833, "v": 0.121}, {"x": 0.0, "y": 3.224, "z": -0.138, "v": 0.04}]}}
{"ts": 1.089, "frame": 3, "num_points_filt": 17, "points_filt": [{"x": -0.153, "y": 2.405, "z": -0.396, "v": 0.04}, {"x": -0.188, "y": 2.509, "z": -1.65, "v": 0.04}, {"x": 0.94, "y": 2.002, "z": 2.039, "v": 0.04}, {"x": 0.098, "y": 3.101, "z": 0.484, "v": 0.04}, {"x": 0.578, "y": 4.54, "z": -0.651, "v": 0.04}, {"x": -0.77, "y": 4.663, "z": 1.393, "v": 0.04}, {"x": -0.519, "y": 5.454, "z": -0.811, "v": 0.04}, {"x": -0.237, "y": 2.473, "z": 0.474, "v": 0.161}, {"x": 0.084, "y": 2.513, "z": -0.992, "v": -0.201}, {"x": 0.084, "y": 2.53, "z": -0.949, "v": -0.121}, {"x": 2.115, "y": 3.007, "z": 2.091, "v": -0.08}, {"x": 0.793, "y": 3.713, "z": -1.864, "v": -0.08}, {"x": 1.319, "y": 2.695, "z": 2.392, "v": -0.04}, {"x": 1.984, "y": 2.92, "z": 1.812, "v": -0.04}, {"x": 1.025, "y": 3.794, "z": -1.166, "v": -0.04}, {"x": -0.64, "y": 3.165, "z": 2.524, "v": -0.04}, {"x": -0.523, "y": 5.372, "z": -1.42, "v": -0.04}], "person": {"present": false}}
{"ts": 1.492, "frame": 4, "num_points_filt": 16, "points_filt": [{"x": -0.185, "y": 2.834, "z": -0.852, "v": 0.04}, {"x": -0.097, "y": 3.057, "z": 0.478, "v": 0.04}, {"x": -1.254, "y": 3.818, "z": 2.999, "v": 0.04}, {"x": -1.087, "y": 5.366, "z": 1.913, "v": 0.04}, {"x": -0.225, "y": 2.375, "z": -0.25, "v": 0.08}, {"x": -0.158, "y": 2.511, "z": -0.254, "v": 0.08}, {"x": 0.194, "y": 3.089, "z": -0.079, "v": 0.161}, {"x": -0.161, "y": 2.541, "z": 0.366, "v": 0.201}, {"x": 0.083, "y": 2.451, "z": -1.029, "v": -0.402}, {"x": 2.434, "y": 2.292, "z": 2.372, "v": -0.322}, {"x": 0.897, "y": 3.859, "z": -1.052, "v": -0.322}, {"x": 0.0, "y": 4.184, "z": -1.749, "v": -0.161}, {"x": 0.0, "y": 2.304, "z": -1.24, "v": -0.04}, {"x": 1.679, "y": 2.494, "z": 2.384, "v": -0.04}, {"x": 1.128, "y": 3.492, "z": -1.622, "v": -0.04}, {"x": 2.33, "y": 2.034, "z": 2.756, "v": -0.04}], "person": {"present": true, "confidence": 0.353, "center": {"x": -0.127, "y": 2.526, "z": -0.252, "v": 0.06}, "num_points": 8, "points": [{"x": -0.158, "y": 2.511, "z": -0.254, "v": 0.08}, {"x": -0.225, "y": 2.375, "z": -0.25, "v": 0.08}, {"x": -0.161, "y": 2.541, "z": 0.366, "v": 0.201}, {"x": 0.194, "y": 3.089, "z": -0.079, "v": 0.161}, {"x": -0.185, "y": 2.834, "z": -0.852, "v": 0.04}, {"x": 0.083, "y": 2.451, "z": -1.029, "v": -0.402}, {"x": -0.097, "y": 3.057, "z": 0.478, "v": 0.04}, {"x": 0.0, "y": 2.304, "z": -1.24, "v": -0.04}]}}

message.txt
20 KB
M. Blackwell — 3/30/2026 12:12 PM
[INFO] Opening ports: CLI=/dev/ttyUSB0 (115200)  DATA=/dev/ttyUSB1 (921600)
[INFO] Running... (Ctrl+C to stop)
{"ts": 0.195, "frame": 1, "num_points_filt": 11, "points_filt": [{"x": 0.0, "y": 2.061, "z": -0.364, "v": 0.04}, {"x": 2.278, "y": 2.36, "z": 1.991, "v": 0.04}, {"x": 0.144, "y": 2.18, "z": -0.753, "v": 0.121}, {"x": 0.086, "y": 2.744, "z": 0.103, "v": 0.121}, {"x": 3.72, "y": 3.987, "z": 1.55, "v": -0.201}, {"x": -3.72, "y": 4.175, "z": -0.93, "v": -0.201}, {"x": -2.099, "y": 4.255, "z": 0.707, "v": -0.161}, {"x": -0.063, "y": 1.888, "z": -0.674, "v": -0.08}, {"x": -0.262, "y": 2.619, "z": -0.929, "v": -0.04}, {"x": 2.253, "y": 2.525, "z": 1.716, "v": -0.04}, {"x": -0.777, "y": 4.263, "z": 2.436, "v": -0.04}], "person": {"present": true, "confidence": 0.42, "center": {"x": -0.031, "y": 2.121, "z": -0.714, "v": 0.0}, "num_points": 4, "points": [{"x": 0.144, "y": 2.18, "z": -0.753, "v": 0.121}, {"x": -0.063, "y": 1.888, "z": -0.674, "v": -0.08}, {"x": 0.0, "y": 2.061, "z": -0.364, "v": 0.04}, {"x": -0.262, "y": 2.619, "z": -0.929, "v": -0.04}]}}
{"ts": 0.587, "frame": 2, "num_points_filt": 15, "points_filt": [{"x": -0.065, "y": 2.052, "z": -0.41, "v": 0.04}, {"x": -0.087, "y": 2.763, "z": -0.386, "v": 0.04}, {"x": -0.128, "y": 4.007, "z": -0.855, "v": 0.121}, {"x": 0.139, "y": 2.175, "z": -0.442, "v": 0.241}, {"x": 3.749, "y": 4.273, "z": -0.565, "v": -0.604}, {"x": -3.392, "y": 4.578, "z": -0.411, "v": -0.604}, {"x": -3.826, "y": 2.743, "z": 0.109, "v": -0.241}, {"x": -2.208, "y": 3.355, "z": 2.46, "v": -0.241}, {"x": -3.692, "y": 4.244, "z": 0.015, "v": -0.201}, {"x": 3.867, "y": 3.856, "z": 1.349, "v": -0.201}, {"x": -1.984, "y": 3.605, "z": 1.906, "v": -0.161}, {"x": -3.685, "y": 2.613, "z": -0.404, "v": -0.161}, {"x": -0.063, "y": 1.844, "z": -0.786, "v": -0.04}, {"x": 1.186, "y": 3.259, "z": -1.538, "v": -0.04}, {"x": 2.253, "y": 2.916, "z": 0.904, "v": -0.04}], "person": {"present": true, "confidence": 0.404, "center": {"x": -0.064, "y": 2.113, "z": -0.426, "v": 0.04}, "num_points": 4, "points": [{"x": -0.065, "y": 2.052, "z": -0.41, "v": 0.04}, {"x": 0.139, "y": 2.175, "z": -0.442, "v": 0.241}, {"x": -0.063, "y": 1.844, "z": -0.786, "v": -0.04}, {"x": -0.087, "y": 2.763, "z": -0.386, "v": 0.04}]}}
{"ts": 0.988, "frame": 3, "num_points_filt": 16, "points_filt": [{"x": 0.067, "y": 2.0, "z": -0.749, "v": 0.0}, {"x": -0.736, "y": 4.429, "z": 1.423, "v": 0.04}, {"x": -0.777, "y": 4.433, "z": 2.111, "v": 0.04}, {"x": 1.087, "y": 4.525, "z": -1.748, "v": 0.04}, {"x": -0.063, "y": 1.837, "z": -0.803, "v": 0.08}, {"x": -1.447, "y": 4.09, "z": 2.767, "v": 0.08}, {"x": 0.089, "y": 2.085, "z": -1.918, "v": 0.121}, {"x": 0.0, "y": 2.672, "z": 1.068, "v": 0.121}, {"x": 0.0, "y": 2.098, "z": -0.407, "v": 0.161}, {"x": -0.24, "y": 3.828, "z": -0.121, "v": 0.241}, {"x": -0.128, "y": 4.058, "z": -0.56, "v": 0.362}, {"x": -2.488, "y": 1.055, "z": -2.407, "v": 0.563}, {"x": -3.516, "y": 4.349, "z": -0.608, "v": -0.402}, {"x": -3.867, "y": 4.005, "z": -0.803, "v": -0.282}, {"x": -2.208, "y": 4.113, "z": 0.626, "v": -0.241}, {"x": 1.172, "y": 3.35, "z": -1.212, "v": -0.04}], "person": {"present": false}}
{"ts": 1.297, "frame": 4, "num_points_filt": 22, "points_filt": [{"x": -0.176, "y": 5.424, "z": -1.479, "v": 0.04}, {"x": 1.41, "y": 4.039, "z": -2.616, "v": 0.08}, {"x": -0.67, "y": 4.814, "z": 2.268, "v": 0.08}, {"x": 0.067, "y": 2.045, "z": -0.616, "v": 0.121}, {"x": -0.649, "y": 5.12, "z": 0.537, "v": 0.121}, {"x": 0.142, "y": 2.144, "z": -0.725, "v": 0.161}, {"x": 0.0, "y": 2.461, "z": -1.316, "v": 0.161}, {"x": -0.067, "y": 2.081, "z": -0.481, "v": 0.201}, {"x": 0.0, "y": 4.278, "z": -0.58, "v": 0.322}, {"x": -2.428, "y": 1.302, "z": -2.21, "v": 0.402}, {"x": -2.318, "y": 1.346, "z": -2.3, "v": 0.523}, {"x": 3.634, "y": 4.124, "z": 0.674, "v": -0.362}, {"x": -3.634, "y": 4.147, "z": -0.512, "v": -0.362}, {"x": -4.106, "y": 3.701, "z": -1.442, "v": -0.362}, {"x": 3.57, "y": 4.201, "z": 1.496, "v": -0.362}, {"x": -3.509, "y": 2.791, "z": 0.265, "v": -0.201}, {"x": -1.965, "y": 3.979, "z": 0.694, "v": -0.201}, {"x": -3.756, "y": 2.202, "z": -1.553, "v": -0.161}, {"x": -2.022, "y": 4.077, "z": 0.807, "v": -0.161}, {"x": 1.199, "y": 3.538, "z": -0.875, "v": -0.08}, {"x": -0.24, "y": 3.141, "z": 2.191, "v": -0.08}, {"x": 2.137, "y": 4.181, "z": 1.344, "v": -0.04}], "person": {"present": true, "confidence": 0.48, "center": {"x": 0.033, "y": 2.112, "z": -0.67, "v": 0.161}, "num_points": 4, "points": [{"x": 0.067, "y": 2.045, "z": -0.616, "v": 0.121}, {"x": 0.142, "y": 2.144, "z": -0.725, "v": 0.161}, {"x": -0.067, "y": 2.081, "z": -0.481, "v": 0.201}, {"x": 0.0, "y": 2.461, "z": -1.316, "v": 0.161}]}}

message.txt
19 KB
[INFO] Running... (Ctrl+C to stop)
{"ts": 0.282, "frame": 1, "num_points_filt": 4, "points_filt": [{"x": 0.0, "y": 2.529, "z": -0.005, "v": 0.04}, {"x": 0.0, "y": 2.303, "z": -1.045, "v": -0.04}, {"x": -1.635, "y": 3.049, "z": -0.448, "v": -0.04}, {"x": -1.724, "y": 4.649, "z": -0.747, "v": -0.04}], "person": {"present": false}}
{"ts": 0.589, "frame": 2, "num_points_filt": 11, "points_filt": [{"x": 0.0, "y": 2.564, "z": -0.218, "v": 0.04}, {"x": 0.098, "y": 2.915, "z": -1.163, "v": 0.04}, {"x": 1.104, "y": 3.606, "z": -1.085, "v": 0.04}, {"x": -1.293, "y": 2.883, "z": -0.385, "v": -0.08}, {"x": -1.635, "y": 2.928, "z": -0.96, "v": -0.08}, {"x": 0.153, "y": 1.929, "z": -1.489, "v": -0.04}, {"x": 0.08, "y": 2.544, "z": -0.377, "v": -0.04}, {"x": -3.303, "y": 1.937, "z": 2.176, "v": -0.04}, {"x": -1.789, "y": 3.584, "z": -1.83, "v": -0.04}, {"x": -3.577, "y": 1.961, "z": 2.079, "v": -0.04}, {"x": -1.717, "y": 3.727, "z": -2.032, "v": -0.04}], "person": {"present": false}}
{"ts": 0.985, "frame": 3, "num_points_filt": 14, "points_filt": [{"x": 0.079, "y": 2.503, "z": -0.355, "v": 0.04}, {"x": 2.33, "y": 3.104, "z": 0.581, "v": 0.04}, {"x": -1.814, "y": 4.33, "z": -2.409, "v": 0.08}, {"x": -2.214, "y": 4.165, "z": -2.731, "v": 0.08}, {"x": -3.017, "y": 1.774, "z": -0.733, "v": 0.523}, {"x": -3.754, "y": 1.693, "z": -0.447, "v": -0.201}, {"x": 3.598, "y": 4.375, "z": -1.024, "v": -0.161}, {"x": -3.262, "y": 3.236, "z": -1.897, "v": -0.121}, {"x": -1.553, "y": 4.266, "z": -2.024, "v": -0.121}, {"x": 0.153, "y": 1.889, "z": -1.54, "v": -0.04}, {"x": 0.0, "y": 2.563, "z": 0.219, "v": -0.04}, {"x": 2.33, "y": 3.049, "z": 0.824, "v": -0.04}, {"x": -1.807, "y": 3.814, "z": -1.403, "v": -0.04}, {"x": -1.86, "y": 3.82, "z": -1.705, "v": -0.04}], "person": {"present": false}}
{"ts": 1.294, "frame": 5, "num_points_filt": 25, "points_filt": [{"x": 0.155, "y": 2.218, "z": -1.112, "v": 0.04}, {"x": 0.164, "y": 2.063, "z": -1.6, "v": 0.04}, {"x": 0.196, "y": 3.05, "z": -0.717, "v": 0.04}, {"x": 2.453, "y": 2.649, "z": 1.539, "v": 0.04}, {"x": 1.104, "y": 3.682, "z": -0.792, "v": 0.04}, {"x": 2.408, "y": 3.123, "z": 0.947, "v": 0.04}, {"x": 1.014, "y": 3.678, "z": -1.376, "v": 0.04}, {"x": -4.023, "y": 2.458, "z": 2.558, "v": 0.161}, {"x": -2.011, "y": 3.987, "z": -2.971, "v": 0.161}, {"x": -2.179, "y": 4.541, "z": -1.845, "v": 0.241}, {"x": -1.104, "y": 3.239, "z": -0.874, "v": 0.282}, {"x": -2.976, "y": 3.379, "z": 0.542, "v": -0.402}, {"x": 0.0, "y": 4.802, "z": -2.079, "v": -0.322}, {"x": -3.867, "y": 3.995, "z": -0.851, "v": -0.282}, {"x": 3.392, "y": 4.369, "z": -1.428, "v": -0.282}, {"x": -3.749, "y": 4.309, "z": -0.105, "v": -0.282}, {"x": -1.275, "y": 2.795, "z": -0.645, "v": -0.241}, {"x": 0.155, "y": 2.143, "z": -1.249, "v": -0.04}, {"x": 0.164, "y": 1.641, "z": -2.032, "v": -0.04}, {"x": 2.33, "y": 2.938, "z": 1.157, "v": -0.04}, {"x": 2.408, "y": 3.185, "z": 0.708, "v": -0.04}, {"x": 1.141, "y": 3.557, "z": -1.579, "v": -0.04}, {"x": -3.441, "y": 1.755, "z": 2.116, "v": -0.04}, {"x": -1.652, "y": 3.567, "z": -1.986, "v": -0.04}, {"x": -1.86, "y": 3.713, "z": -1.928, "v": -0.04}], "person": {"present": true, "confidence": 0.439, "center": {"x": 0.159, "y": 2.103, "z": -1.425, "v": 0.0}, "num_points": 4, "points": [{"x": 0.164, "y": 2.063, "z": -1.6, "v": 0.04}, {"x": 0.155, "y": 2.143, "z": -1.249, "v": -0.04}, {"x": 0.155, "y": 2.218, "z": -1.112, "v": 0.04}, {"x": 0.164, "y": 1.641, "z": -2.032, "v": -0.04}]}}
{"ts": 1.786, "frame": 6, "num_points_filt": 16, "points_filt": [{"x": 0.155, "y": 2.2, "z": -1.146, "v": 0.04}, {"x": 0.083, "y": 2.572, "z": -0.673, "v": 0.04}, {"x": 0.099, "y": 2.889, "z": -1.333, "v": 0.04}, {"x": -1.117, "y": 3.144, "z": -1.286, "v": 0.161}, {"x": -4.088, "y": 1.667, "z": 2.809, "v": 0.241}, {"x": -1.962, "y": 4.397, "z": -2.049, "v": 0.241}, {"x": -4.19, "y": 2.353, "z": 2.382, "v": 0.241}, {"x": -2.179, "y": 4.021, "z": -2.803, "v": 0.241}, {"x": -2.807, "y": 3.373, "z": 0.958, "v": -0.563}, {"x": -1.258, "y": 2.737, "z": -0.714, "v": -0.362}, {"x": -3.234, "y": 3.132, "z": -2.003, "v": -0.201}, {"x": -1.54, "y": 3.81, "z": -2.719, "v": -0.201}, {"x": 2.33, "y": 2.943, "z": 1.146, "v": -0.04}, {"x": 1.141, "y": 3.731, "z": -1.108, "v": -0.04}, {"x": -3.441, "y": 1.349, "z": 2.396, "v": -0.04}, {"x": -1.789, "y": 3.633, "z": -1.731, "v": -0.04}], "person": {"present": false}}

message.txt
17 KB
[INFO] Opening ports: CLI=/dev/ttyUSB0 (115200)  DATA=/dev/ttyUSB1 (921600)
[INFO] Running... (Ctrl+C to stop)
{"ts": 0.283, "frame": 1, "num_points_filt": 12, "points_filt": [{"x": -3.148, "y": 3.278, "z": 0.554, "v": 0.0}, {"x": -0.362, "y": 4.991, "z": -2.932, "v": 0.0}, {"x": -0.068, "y": 2.176, "z": -0.127, "v": 0.04}, {"x": -0.491, "y": 3.352, "z": 1.981, "v": 0.08}, {"x": 0.981, "y": 3.321, "z": -1.847, "v": 0.08}, {"x": -0.507, "y": 3.268, "z": 2.347, "v": 0.08}, {"x": 1.141, "y": 3.687, "z": -1.245, "v": 0.08}, {"x": -0.253, "y": 2.351, "z": -1.311, "v": -0.04}, {"x": 0.76, "y": 2.136, "z": 1.472, "v": -0.04}, {"x": -0.365, "y": 2.512, "z": -1.446, "v": -0.04}, {"x": 0.913, "y": 2.213, "z": 1.674, "v": -0.04}, {"x": -0.891, "y": 4.578, "z": 0.916, "v": -0.04}], "person": {"present": false}}
{"ts": 0.683, "frame": 2, "num_points_filt": 12, "points_filt": [{"x": -0.368, "y": 3.255, "z": 2.162, "v": 0.04}, {"x": 1.226, "y": 3.448, "z": -1.418, "v": 0.04}, {"x": -3.291, "y": 3.046, "z": 0.926, "v": 0.04}, {"x": -0.362, "y": 5.072, "z": -2.79, "v": 0.04}, {"x": 0.142, "y": 2.195, "z": -0.551, "v": 0.201}, {"x": -0.067, "y": 2.124, "z": -0.219, "v": -0.04}, {"x": 0.0, "y": 2.263, "z": -0.137, "v": -0.04}, {"x": -0.169, "y": 2.553, "z": -0.873, "v": -0.04}, {"x": 0.093, "y": 2.571, "z": -1.475, "v": -0.04}, {"x": 1.205, "y": 1.474, "z": 2.273, "v": -0.04}, {"x": -3.291, "y": 3.072, "z": 0.835, "v": -0.04}, {"x": -0.362, "y": 4.958, "z": -2.987, "v": -0.04}], "person": {"present": true, "confidence": 0.482, "center": {"x": 0.0, "y": 2.195, "z": -0.219, "v": -0.04}, "num_points": 3, "points": [{"x": -0.067, "y": 2.124, "z": -0.219, "v": -0.04}, {"x": 0.0, "y": 2.263, "z": -0.137, "v": -0.04}, {"x": 0.142, "y": 2.195, "z": -0.551, "v": 0.201}]}}
{"ts": 1.082, "frame": 3, "num_points_filt": 5, "points_filt": [{"x": -0.362, "y": 4.997, "z": -2.921, "v": 0.0}, {"x": -0.273, "y": 2.137, "z": 0.335, "v": 0.04}, {"x": -3.291, "y": 3.116, "z": 0.652, "v": 0.04}, {"x": 0.346, "y": 4.915, "z": -2.529, "v": 0.04}, {"x": -0.18, "y": 1.823, "z": -2.219, "v": -0.121}], "person": {"present": false}}
{"ts": 1.485, "frame": 5, "num_points_filt": 10, "points_filt": [{"x": -0.589, "y": 4.358, "z": 1.686, "v": 0.04}, {"x": 1.221, "y": 4.322, "z": -1.919, "v": 0.04}, {"x": 0.0, "y": 4.202, "z": -0.778, "v": -0.201}, {"x": 0.0, "y": 2.131, "z": -0.16, "v": -0.121}, {"x": 0.213, "y": 1.977, "z": -1.089, "v": -0.121}, {"x": -0.368, "y": 3.023, "z": 2.476, "v": -0.121}, {"x": -0.274, "y": 2.398, "z": -1.646, "v": -0.08}, {"x": -0.142, "y": 2.245, "z": 0.282, "v": -0.04}, {"x": -0.349, "y": 2.058, "z": -1.852, "v": -0.04}, {"x": 0.785, "y": 2.493, "z": 0.978, "v": -0.04}], "person": {"present": false}}

message.txt
14 KB
M. Blackwell — 3/30/2026 12:21 PM
(RADIAN_env) mblackwell31@RADIANPi:~/RADIAN/fall_detector $ python3 fall_detector_v2.py \
  --parser     mmwave_run6.py \
  --model      best_model_pi_v3.pkl \
  --cli-port   /dev/ttyUSB0 \
  --data-port  /dev/ttyUSB1 \
  --cfg-file   config3.cfg \

message.txt
6 KB
AndySalad — 3/30/2026 12:25 PM
python3 fall_detector_v2.py \
  --parser     mmwave_run6.py \
  --model      best_model_pi_v3.pkl \
  --cli-port   /dev/ttyUSB0 \
  --data-port  /dev/ttyUSB1 \
  --cfg-file   config3.cfg \
  --threshold  0.55 \
  --confirm    3 \
  --gotify-url   http://your_server:8080/ \
  --gotify-token YOUR_TOKEN \
  --verbose
AndySalad — 3/30/2026 1:25 PM
Attachment file type: unknown
best_model_pi_v4.pkl
252.66 KB
python3 fall_detector_v2.py \
  --parser     mmwave_run6.py \
  --model      best_model_pi_v4.pkl \
  --cli-port   /dev/ttyUSB0 \
  --data-port  /dev/ttyUSB1 \
  --cfg-file   config3.cfg \
  --gotify-url   http://your_server:8080/ \
  --gotify-token YOUR_TOKEN \
  --verbose
M. Blackwell — 3/30/2026 1:32 PM
[INFO] Opening ports: CLI=/dev/ttyUSB0 (115200)  DATA=/dev/ttyUSB1 (921600)
[INFO] Running... (Ctrl+C to stop)
{"ts": 0.287, "frame": 1, "num_points_filt": 7, "points_filt": [{"x": 0.97, "y": 3.412, "z": -1.574, "v": 0.04}, {"x": -0.065, "y": 2.081, "z": -0.218, "v": -0.04}, {"x": -0.069, "y": 2.205, "z": -0.284, "v": -0.04}, {"x": -0.183, "y": 2.563, "z": 1.39, "v": -0.04}, {"x": -0.613, "y": 3.413, "z": 1.838, "v": -0.04}, {"x": -0.275, "y": 4.365, "z": -0.516, "v": -0.04}, {"x": -0.47, "y": 4.979, "z": -0.373, "v": -0.04}], "person": {"present": false}}
{"ts": 0.784, "frame": 3, "num_points_filt": 8, "points_filt": [{"x": -0.208, "y": 2.023, "z": 0.901, "v": 0.04}, {"x": 3.72, "y": 1.38, "z": -0.039, "v": 0.04}, {"x": -0.316, "y": 5.044, "z": 0.204, "v": 0.08}, {"x": -0.486, "y": 5.097, "z": 0.844, "v": 0.08}, {"x": 0.069, "y": 2.009, "z": -0.95, "v": 0.241}, {"x": 1.187, "y": 2.703, "z": -0.04, "v": -0.364}, {"x": 3.336, "y": 1.949, "z": -0.04, "v": 1.213}, {"x": 3.013, "y": 2.601, "z": -0.04, "v": 3.51}], "person": {"present": false}}
{"ts": 1.285, "frame": 5, "num_points_filt": 10, "points_filt": [{"x": 0.97, "y": 3.469, "z": -1.444, "v": 0.04}, {"x": -0.485, "y": 3.083, "z": 2.307, "v": 0.04}, {"x": -0.364, "y": 3.004, "z": 2.43, "v": 0.121}, {"x": 0.0, "y": 2.174, "z": -0.785, "v": -0.282}, {"x": -0.204, "y": 2.17, "z": -0.062, "v": -0.04}, {"x": -0.54, "y": 1.951, "z": -2.046, "v": -0.04}, {"x": 0.45, "y": 2.804, "z": 0.468, "v": -0.04}, {"x": -0.485, "y": 3.308, "z": 1.97, "v": -0.04}, {"x": -0.507, "y": 3.512, "z": 1.964, "v": -0.04}, {"x": 0.174, "y": 5.133, "z": -2.186, "v": -0.04}], "person": {"present": true, "confidence": 0.427, "center": {"x": -0.485, "y": 3.196, "z": 2.138, "v": 0.0}, "num_points": 4, "points": [{"x": -0.485, "y": 3.083, "z": 2.307, "v": 0.04}, {"x": -0.485, "y": 3.308, "z": 1.97, "v": -0.04}, {"x": -0.507, "y": 3.512, "z": 1.964, "v": -0.04}, {"x": -0.364, "y": 3.004, "z": 2.43, "v": 0.121}]}}
{"ts": 1.682, "frame": 6, "num_points_filt": 6, "points_filt": [{"x": -0.064, "y": 2.048, "z": -0.024, "v": 0.04}, {"x": 1.104, "y": 3.41, "z": -1.599, "v": 0.04}, {"x": 1.656, "y": 2.134, "z": 2.276, "v": -0.322}, {"x": 0.221, "y": 3.496, "z": -0.449, "v": -0.322}, {"x": -0.368, "y": 3.202, "z": 2.24, "v": -0.121}, {"x": 2.306, "y": 1.587, "z": 2.994, "v": -0.121}], "person": {"present": false}}

message.txt
18 KB
(RADIAN_env) mblackwell31@RADIANPi:~/RADIAN/fall_detector $ python3 mmwave_run6.py | head -20
[INFO] Opening ports: CLI=/dev/ttyUSB0 (115200)  DATA=/dev/ttyUSB1 (921600)
[INFO] Running... (Ctrl+C to stop)
{"ts": 0.385, "frame": 1, "num_points_filt": 4, "points_filt": [{"x": -0.079, "y": 2.473, "z": -0.522, "v": 0.04}, {"x": 0.083, "y": 2.61, "z": -0.505, "v": 0.04}, {"x": 1.014, "y": 3.911, "z": -0.353, "v": 0.04}, {"x": 0.0, "y": 2.431, "z": -0.697, "v": -0.04}], "person": {"present": true, "confidence": 0.457, "center": {"x": 0.0, "y": 2.473, "z": -0.522, "v": 0.04}, "num_points": 3, "points": [{"x": -0.079, "y": 2.473, "z": -0.522, "v": 0.04}, {"x": 0.083, "y": 2.61, "z": -0.505, "v": 0.04}, {"x": 0.0, "y": 2.431, "z": -0.697, "v": -0.04}]}}
{"ts": 0.887, "frame": 2, "num_points_filt": 3, "points_filt": [{"x": -0.079, "y": 2.483, "z": -0.474, "v": 0.04}, {"x": 0.0, "y": 2.439, "z": -0.67, "v": -0.04}, {"x": 0.887, "y": 3.777, "z": -1.182, "v": -0.04}], "person": {"present": false}}
{"ts": 1.39, "frame": 4, "num_points_filt": 7, "points_filt": [{"x": 0.078, "y": 2.354, "z": -0.793, "v": 0.04}, {"x": 0.0, "y": 2.411, "z": -1.123, "v": 0.04}, {"x": 0.21, "y": 3.342, "z": -0.242, "v": 0.04}, {"x": 1.014, "y": 3.801, "z": -0.986, "v": 0.04}, {"x": -0.634, "y": 3.177, "z": 2.439, "v": 0.04}, {"x": 0.0, "y": 2.302, "z": -1.332, "v": -0.04}, {"x": 1.025, "y": 3.678, "z": -1.49, "v": -0.04}], "person": {"present": true, "confidence": 0.431, "center": {"x": 0.0, "y": 2.354, "z": -1.123, "v": 0.04}, "num_points": 3, "points": [{"x": 0.0, "y": 2.411, "z": -1.123, "v": 0.04}, {"x": 0.0, "y": 2.302, "z": -1.332, "v": -0.04}, {"x": 0.078, "y": 2.354, "z": -0.793, "v": 0.04}]}}

message.txt
16 KB
AndySalad — 3/30/2026 1:37 PM
Attachment file type: unknown
best_model_pi_v5.pkl
56.88 KB
python3 fall_detector_v2.py \
  --parser     mmwave_run6.py \
  --model      best_model_pi_v5.pkl \
  --cli-port   /dev/ttyUSB0 \
  --data-port  /dev/ttyUSB1 \
  --cfg-file   config3.cfg \
  --gotify-url   http://your_server:8080/ \
  --gotify-token YOUR_TOKEN \
  --verbose
AndySalad — 3/30/2026 1:45 PM
nano buzzer_test.py
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.OUT)

GPIO.output(27, GPIO.HIGH)
time.sleep(0.5)
GPIO.output(27, GPIO.LOW)

GPIO.cleanup()
sudo python3 buzzer_test.py
AndySalad — 8:15 AM
cd /home/mblackwell31/RADIAN/fall_detector && python3 fall_detector_v2.py --parser mmwave_run6.py --model best_model_pi_v9.pkl --cli-port /dev/ttyUSB0 --data-port /dev/ttyUSB1 --cfg-file config3.cfg --gotify-url http://your_server:8080/ --gotify-token YOUR_TOKEN &
[Unit]
Description=RADIAN Fall Detector
After=network.target

[Service]
Type=simple
User=mblackwell31
WorkingDirectory=/home/mblackwell31/RADIAN/fall_detector
ExecStart=/usr/bin/python3 fall_detector_v2.py \
  --parser mmwave_run6.py \
  --model best_model_pi_v9.pkl \
  --cli-port /dev/ttyUSB0 \
  --data-port /dev/ttyUSB1 \
  --cfg-file config3.cfg \
  --gotify-url http://your_server:8080/ \
  --gotify-token YOUR_TOKEN \
  --verbose
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
M. Blackwell — 8:20 AM
● radian.service - RADIAN Fall Detector
     Loaded: loaded (/etc/systemd/system/radian.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-04-02 08:20:03 CDT; 6s ago
 Invocation: c9ce21836dbc414485d80ac6c470d2bc
   Main PID: 2579 (python3)
      Tasks: 4 (limit: 751)
        CPU: 3.626s
     CGroup: /system.slice/radian.service
             └─2579 /usr/bin/python3 fall_detector_v2.py --parser mmwave_run6.py --model best_model_pi_v9.pkl --cli-por>

Apr 02 08:20:03 mblackwell31 systemd[1]: Started radian.service - RADIAN Fall Detector.
Apr 02 08:20:09 mblackwell31 python3[2579]: 08:20:09 [INFO] Loading model: best_model_pi_v9.pkl
lines 1-12/12 (END)
AndySalad — 8:20 AM
See live logs
sudo journalctl -u radian -f

Stop it
sudo systemctl stop radian

Restart it
sudo systemctl restart radian

Disable autostart
sudo systemctl disable radian
AndySalad — 9:09 AM
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

fall_detector_v2.py
31 KB
M. Blackwell — 9:30 AM
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

message.txt
30 KB
Thats four ^
That's five ^
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

message.txt
30 KB
AndySalad — 9:32 AM
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

Architecture
------------
                    ┌─────────────────────┐
                    │   mmwave_run6.py     │  (subprocess)
                    │  CLI_PORT + DATA_PORT│
                    │  → JSON to stdout   │
                    └────────┬────────────┘
                             │ one JSON line per radar frame
                    ┌────────▼────────────┐
                    │  reader thread       │
                    │  deque(maxlen=WINDOW)│
                    └────────┬────────────┘
                             │ every STEP new frames
                    ┌────────▼────────────┐
                    │  inference thread    │
                    │  extract_features()  │
                    │  ET-30 model         │
                    └────────┬────────────┘
                             │ prob >= threshold
                    ┌────────▼────────────┐
                    │  Gotify alert        │
                    │  CSV log             │
                    └─────────────────────┘

Usage
-----
    python3 fall_detector.py \\
        --parser    mmwave_run6.py \\
        --model     best_model_pi_v3.pkl \\
        --cli-port  /dev/ttyUSB0 \\
        --data-port /dev/ttyUSB1 \\
        --cfg-file  config3.cfg \\
        --gotify-url  http://YOUR_SERVER:PORT \\
        --gotify-token YOUR_APP_TOKEN \\
        --verbose

Options
-------
  --parser        PATH   Path to mmwave_run6.py            [required]
  --model         PATH   Path to best_model_pi_v3.pkl      [required]
  --cli-port      PORT   Radar CLI/config UART port        [default: /dev/ttyUSB0]
  --data-port     PORT   Radar data UART port              [default: /dev/ttyUSB1]
  --cfg-file      PATH   Radar .cfg file                   [default: config3.cfg]
  --window        INT    Frames per inference window       [default: 32]
  --step          INT    New frames between inferences     [default: 6]
  --cooldown      FLOAT  Min seconds between alerts        [default: 15.0]
  --gotify-url    URL    Gotify server base URL            [default: None]
  --gotify-token  TOKEN  Gotify app token                  [default: None]
  --log           PATH   CSV log file path                 [default: fall_log.csv]
  --verbose              Print every inference result
"""

import argparse
import collections
import csv
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

import joblib
import numpy as np
import pandas as pd

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── optional GPIO buzzer ──────────────────────────────────────────────────────
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(27, GPIO.OUT)
    GPIO.output(27, GPIO.LOW)
    HAS_GPIO = True
except Exception:
    HAS_GPIO = False

# ── optional debug dashboard ──────────────────────────────────────────────────
try:
    from debug_dashboard import Dashboard, DebugState
    HAS_DEBUG = True
except ImportError:
    HAS_DEBUG = False

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
... (588 lines left)

fall_detector_v2 (1).py
31 KB
﻿
AndySalad
andysalad5654
 
"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

Architecture
------------
                    ┌─────────────────────┐
                    │   mmwave_run6.py     │  (subprocess)
                    │  CLI_PORT + DATA_PORT│
                    │  → JSON to stdout   │
                    └────────┬────────────┘
                             │ one JSON line per radar frame
                    ┌────────▼────────────┐
                    │  reader thread       │
                    │  deque(maxlen=WINDOW)│
                    └────────┬────────────┘
                             │ every STEP new frames
                    ┌────────▼────────────┐
                    │  inference thread    │
                    │  extract_features()  │
                    │  ET-30 model         │
                    └────────┬────────────┘
                             │ prob >= threshold
                    ┌────────▼────────────┐
                    │  Gotify alert        │
                    │  CSV log             │
                    └─────────────────────┘

Usage
-----
    python3 fall_detector.py \\
        --parser    mmwave_run6.py \\
        --model     best_model_pi_v3.pkl \\
        --cli-port  /dev/ttyUSB0 \\
        --data-port /dev/ttyUSB1 \\
        --cfg-file  config3.cfg \\
        --gotify-url  http://YOUR_SERVER:PORT \\
        --gotify-token YOUR_APP_TOKEN \\
        --verbose

Options
-------
  --parser        PATH   Path to mmwave_run6.py            [required]
  --model         PATH   Path to best_model_pi_v3.pkl      [required]
  --cli-port      PORT   Radar CLI/config UART port        [default: /dev/ttyUSB0]
  --data-port     PORT   Radar data UART port              [default: /dev/ttyUSB1]
  --cfg-file      PATH   Radar .cfg file                   [default: config3.cfg]
  --window        INT    Frames per inference window       [default: 32]
  --step          INT    New frames between inferences     [default: 6]
  --cooldown      FLOAT  Min seconds between alerts        [default: 15.0]
  --gotify-url    URL    Gotify server base URL            [default: None]
  --gotify-token  TOKEN  Gotify app token                  [default: None]
  --log           PATH   CSV log file path                 [default: fall_log.csv]
  --verbose              Print every inference result
"""

import argparse
import collections
import csv
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

import joblib
import numpy as np
import pandas as pd

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── optional GPIO buzzer ──────────────────────────────────────────────────────
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(27, GPIO.OUT)
    GPIO.output(27, GPIO.LOW)
    HAS_GPIO = True
except Exception:
    HAS_GPIO = False

# ── optional debug dashboard ──────────────────────────────────────────────────
try:
    from debug_dashboard import Dashboard, DebugState
    HAS_DEBUG = True
except ImportError:
    HAS_DEBUG = False

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("fall_detector")

# ── constants ─────────────────────────────────────────────────────────────────
N_BUCKETS = 8


# ═══════════════════════════════════════════════════════════════════════════════
# Feature extraction — must stay byte-for-byte identical to train_fall_model_v3.py
# ═══════════════════════════════════════════════════════════════════════════════

def _longest_run(cond) -> int:
    best = cur = 0
    for c in cond:
        if c:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _safe_stats(arr, prefix: str) -> dict:
    arr = np.asarray(arr, dtype=float)
    if len(arr) == 0:
        keys = ["mean", "std", "min", "max", "median",
                "q10", "q25", "q75", "q90", "range", "skew", "kurtosis"]
        return {f"{prefix}_{k}": 0.0 for k in keys}
    n   = len(arr)
    mu  = arr.mean()
    std = max(arr.std(ddof=0), 1e-12)
    skew = float(((arr - mu) ** 3).mean() / std ** 3) if n > 2 else 0.0
    kurt = float(((arr - mu) ** 4).mean() / std ** 4 - 3) if n > 3 else 0.0
    return {
        f"{prefix}_mean"    : float(mu),
        f"{prefix}_std"     : float(std),
        f"{prefix}_min"     : float(arr.min()),
        f"{prefix}_max"     : float(arr.max()),
        f"{prefix}_median"  : float(np.median(arr)),
        f"{prefix}_q10"     : float(np.quantile(arr, 0.10)),
        f"{prefix}_q25"     : float(np.quantile(arr, 0.25)),
        f"{prefix}_q75"     : float(np.quantile(arr, 0.75)),
        f"{prefix}_q90"     : float(np.quantile(arr, 0.90)),
        f"{prefix}_range"   : float(arr.max() - arr.min()),
        f"{prefix}_skew"    : skew,
        f"{prefix}_kurtosis": kurt,
    }


def _spectral(arr, prefix: str, n_freqs: int = 4) -> dict:
    arr = np.asarray(arr, dtype=float)
    feats: dict = {}
    if len(arr) < 4:
        for i in range(n_freqs):
            feats[f"{prefix}_fft_{i}"] = 0.0
        feats[f"{prefix}_spec_ent"] = 0.0
        return feats
    fft = np.abs(np.fft.rfft(arr - arr.mean()))[:n_freqs]
    for i, val in enumerate(fft):
        feats[f"{prefix}_fft_{i}"] = float(val)
    p = fft ** 2 + 1e-12
    p /= p.sum()
    feats[f"{prefix}_spec_ent"] = float(-np.sum(p * np.log(p)))
    return feats


def _buckets(arr, prefix: str, n: int = N_BUCKETS) -> dict:
    arr    = np.asarray(arr, dtype=float)
    splits = np.array_split(arr, n) if len(arr) else [np.array([0.0])] * n
    return {
        f"{prefix}_b{i}": float(s.mean()) if len(s) else 0.0
        for i, s in enumerate(splits)
    }


def _smooth(arr, w: int = 5) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    if   len(arr) >= w: return np.convolve(arr, np.ones(w) / w, mode="same")
    elif len(arr) >= 3: return np.convolve(arr, np.ones(3) / 3, mode="same")
    return arr.copy()


def extract_features(frames: list) -> dict:
    """
    frames  : list of dicts from mmwave_run6.py stdout, each containing:
                  ts, frame, num_points_filt, points_filt, person
    Returns : feature dict aligned with training feature_cols
    """
    zmean, zmed, zmin_, zmax_, ziqr = [], [], [], [], []
    vmean, vpeak, vmed              = [], [], []
    xspread, yspread, zspread       = [], [], []
    npts_arr, ppres                  = [], []
    bvol, vposfrac                  = [], []
    cx_arr, cy_arr                  = [], []

    for r in frames:
        pts = r.get("points_filt", []) or []
        npts_arr.append(float(r.get("num_points_filt", len(pts))))
        ppres.append(float(bool((r.get("person") or {}).get("present", False))))

        if pts:
            xa = np.array([p["x"] for p in pts], dtype=float)
            ya = np.array([p["y"] for p in pts], dtype=float)
            za = np.array([p["z"] for p in pts], dtype=float)
            va = np.array([p["v"] for p in pts], dtype=float)
            av = np.abs(va)

            zmean.append(za.mean());  zmed.append(np.median(za))
            zmin_.append(za.min());   zmax_.append(za.max())
            ziqr.append(np.quantile(za, 0.75) - np.quantile(za, 0.25))
            vmean.append(av.mean());  vpeak.append(av.max()); vmed.append(np.median(av))
            xspread.append(xa.std()); yspread.append(ya.std()); zspread.append(za.std())
            cx_arr.append(xa.mean()); cy_arr.append(ya.mean())
            bvol.append(
                (xa.max() - xa.min() + 1e-6)
                * (ya.max() - ya.min() + 1e-6)
                * (za.max() - za.min() + 1e-6)
            )
            vposfrac.append(float((va > 0).mean()))
        else:
            for lst in [zmean, zmed, zmin_, zmax_, ziqr,
                        vmean, vpeak, vmed, xspread, yspread, zspread,
                        cx_arr, cy_arr, bvol, vposfrac]:
                lst.append(0.0)

    z  = np.array(zmean); v = np.array(vmean)
    zs = _smooth(z, 5);   vs = _smooth(v, 5)
    dz  = np.diff(zs, prepend=zs[0])
    dv  = np.diff(vs, prepend=vs[0])
    ddz = np.diff(dz, prepend=dz[0])
    adz = np.abs(dz); adv = np.abs(dv)

    cx  = _smooth(np.array(cx_arr), 3)
    cy  = _smooth(np.array(cy_arr), 3)
    lat = np.sqrt(
        np.abs(np.diff(cx, prepend=cx[0])) ** 2
        + np.abs(np.diff(cy, prepend=cy[0])) ** 2
    )

    imin  = int(np.argmin(zs)) if len(zs) else 0
    imax  = int(np.argmax(vs)) if len(vs) else 0
    post  = min(len(zs), imin + 6)
    z_rec = float(zs[imin + 1 : post].mean() - zs[imin]) if post > imin + 1 else 0.0

    feats: dict = {}

    for arr, prefix in [
        (zmean,   "zmean"),  (zmed,    "zmed"),  (zmin_,   "zmin"),
        (zmax_,   "zmax"),   (ziqr,    "ziqr"),  (vmean,   "vmean"),
        (vpeak,   "vpeak"),  (vmed,    "vmed"),  (npts_arr,"npts"),
        (xspread, "xspread"),(yspread, "yspread"),(zspread,"zspread"),
        (adz,     "abs_dz"), (adv,     "abs_dv"), (ddz,    "jerk"),
        (bvol,    "bvol"),   (vposfrac,"vposfrac"),(lat,   "lat_motion"),
    ]:
        feats.update(_safe_stats(arr, prefix))

    feats.update(_spectral(zs,  "z"))
    feats.update(_spectral(vs,  "v"))
    feats.update(_spectral(adz, "dz"))

    feats.update(_buckets(zs,  "z"))
    feats.update(_buckets(vs,  "v"))
    feats.update(_buckets(adz, "dz"))
    feats.update(_buckets(dz,  "dz_signed"))

    feats["n_frames"]             = len(frames)
    feats["z_drop"]               = float(zs.max() - zs.min())       if len(zs) else 0.0
    feats["z_signed_drop"]        = float(zs[0]  - zs.min())          if len(zs) else 0.0
    feats["z_end_minus_start"]    = float(zs[-1]  - zs[0])            if len(zs) else 0.0
    feats["z_end_minus_min"]      = float(zs[-1]  - zs.min())          if len(zs) else 0.0
    feats["z_min_index_frac"]     = float(imin / max(1, len(zs) - 1))
    feats["v_peak_index_frac"]    = float(imax / max(1, len(vs) - 1))
    feats["v_peak"]               = float(vs.max())                    if len(vs) else 0.0
    feats["dz_peak"]              = float(adz.max())                   if len(adz) else 0.0
    feats["dv_peak"]              = float(adv.max())                   if len(adv) else 0.0
    feats["jerk_peak"]            = float(np.abs(ddz).max())           if len(ddz) else 0.0
    feats["impulse_score"]        = feats["z_signed_drop"] * feats["v_peak"]
    feats["impulse2"]             = feats["z_drop"]        * feats["v_peak"]
    feats["v_energy"]             = float((vs ** 2).sum())
    feats["z_recovery"]           = z_rec
    feats["v_leads_z_drop"]       = float(imax < imin)
    feats["v_z_lead_diff"]        = float(imin - imax) / max(1, len(zs))
    feats["high_v_run"]           = _longest_run(vs  > np.quantile(vs,  0.8)) if len(vs)  else 0
    feats["high_dz_run"]          = _longest_run(adz > np.quantile(adz, 0.8)) if len(adz) else 0
    feats["low_z_run"]            = _longest_run(zs  < np.quantile(zs,  0.2)) if len(zs)  else 0
    pp = np.array(ppres)
    feats["person_present_mean"]  = float(pp.mean())
    feats["person_present_change"]= float(np.abs(np.diff(pp)).sum())
    feats["z_curvature_mean"]     = float(np.abs(ddz).mean())          if len(ddz) else 0.0
    bv = np.array(bvol)
    feats["bvol_drop"]            = float(bv.max() - bv.min())         if len(bv) else 0.0
    feats["bvol_end_ratio"]       = float(bv[-1] / (bv.max() + 1e-6))  if len(bv) else 1.0
    feats["lat_vs_z_ratio"]       = float(lat.mean() / (adz.mean() + 1e-6))

    return feats


# ═══════════════════════════════════════════════════════════════════════════════
# Gotify alert
# ═══════════════════════════════════════════════════════════════════════════════

def send_gotify_alert(url: str, token: str, prob: float, ts: str):
    if not HAS_REQUESTS:
        log.warning("requests not installed — cannot send Gotify alert. Run: pip install requests")
        return
    try:
        resp = requests.post(
            f"{url.rstrip('/')}/message",
            params={"token": token},
            json={
                "title"   : "⚠️ Fall Detected",
                "message" : f"Fall detected ({prob:.0%} confidence) at {ts}",
                "priority": 8,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            log.info(f"Gotify alert sent  ({prob:.0%})")
        else:
            log.warning(f"Gotify returned HTTP {resp.status_code}: {resp.text[:120]}")
    except Exception as e:
        log.error(f"Gotify alert failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CSV logger
# ═══════════════════════════════════════════════════════════════════════════════

class FallLogger:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                csv.writer(f).writerow(
                    ["timestamp", "prediction", "probability", "alert_sent"]
                )

    def write(self, ts: str, pred: int, prob: float, alerted: bool):
        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow([ts, pred, f"{prob:.4f}", int(alerted)])


# ═══════════════════════════════════════════════════════════════════════════════
# Main detector
# ═══════════════════════════════════════════════════════════════════════════════

class FallDetector:
    def __init__(self, args):
        self.args = args

        # Load model bundle
        log.info(f"Loading model: {args.model}")
        bundle            = joblib.load(args.model)
        self.model        = bundle["model"]
        self.feature_cols = bundle["feature_cols"]
        self.threshold    = bundle["threshold"]
        log.info(
            f"Model ready — {len(self.feature_cols)} features, "
            f"threshold={self.threshold:.2f}"
        )

        # Sliding window buffer
        self.window = collections.deque(maxlen=args.window)
        self.logger = FallLogger(args.log)

        # State
        self._frame_count = 0
        self._last_infer  = 0
        self._last_alert  = 0.0
        self._running     = False
        self._lock        = threading.Lock()

        # Stats
        self.stats = {
            "frames": 0, "inferences": 0,
            "falls_flagged": 0, "alerts_sent": 0,
            "parse_errors": 0,
        }

        # Debug dashboard (only active when --debug is passed)
        self._debug_state = None
        self._dashboard   = None
        if getattr(args, "debug", False):
            if HAS_DEBUG:
                self._debug_state = DebugState(args.window)
                self._dashboard   = Dashboard(self._debug_state, self.threshold)
            else:
                log.warning("debug_dashboard.py not found — --debug has no effect")

    # ── inference ──────────────────────────────────────────────────────────────

    def _infer(self) -> tuple:
        with self._lock:
            window_snap = list(self.window)

        feats = extract_features(window_snap)
        X     = pd.DataFrame(
            [[feats.get(col, 0.0) for col in self.feature_cols]],
            columns=self.feature_cols,
        )
        prob = float(self.model.predict_proba(X)[0, 1])
        pred = int(prob >= self.threshold)
        return prob, pred

    # ── alert ──────────────────────────────────────────────────────────────────

    def _maybe_alert(self, prob: float, ts: str) -> bool:
        now = time.time()
        if now - self._last_alert < self.args.cooldown:
            return False
        self._last_alert = now
        log.warning(f"🚨 FALL DETECTED  confidence={prob:.1%}  time={ts}")
        # Buzz the buzzer
        if HAS_GPIO:
            try:
                import threading, time as _time
                def _buzz():
                    for _ in range(3):
                        GPIO.output(27, GPIO.HIGH)
                        _time.sleep(0.3)
                        GPIO.output(27, GPIO.LOW)
                        _time.sleep(0.2)
                threading.Thread(target=_buzz, daemon=True).start()
            except Exception as e:
                log.debug(f"Buzzer error: {e}")
        if self.args.gotify_url and self.args.gotify_token:
            send_gotify_alert(
                self.args.gotify_url, self.args.gotify_token, prob, ts
            )
        self.stats["alerts_sent"] += 1
        return True

    # ── reader thread: launches mmwave_run6.py, reads its stdout ───────────────

    def _reader_thread(self):
        cmd = [
            sys.executable, self.args.parser,
        ]

        # Pass port/cfg overrides via environment variables that mmwave_run6.py
        # respects, then patch CLI_PORT / DATA_PORT / CFG_FILE at the top of
        # the script via a tiny wrapper approach.
        # Simpler: we just patch the three settings by rewriting them in the
        # subprocess environment isn't possible for hardcoded vars, so we
        # launch with a monkeypatch env trick via -c.

        patch = (
            f"import mmwave_run6 as m; "
            f"m.CLI_PORT='{self.args.cli_port}'; "
            f"m.DATA_PORT='{self.args.data_port}'; "
            f"m.CFG_FILE='{self.args.cfg_file}'; "
            f"m.main()"
        )
        cmd = [sys.executable, "-c", patch]

        # Make sure the directory containing mmwave_run6.py is on the path
        parser_dir = os.path.dirname(os.path.abspath(self.args.parser))

        log.info(f"Starting parser: {self.args.parser}")
        log.info(f"  CLI  port : {self.args.cli_port}")
        log.info(f"  Data port : {self.args.data_port}")
        log.info(f"  Config    : {self.args.cfg_file}")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,   # parser's status logs go here
                text=True,
                cwd=parser_dir,
                env={**os.environ, "PYTHONPATH": parser_dir},
            )
            self._proc = proc

            # Forward parser's stderr to our log at DEBUG level
            def _forward_stderr():
                for line in proc.stderr:
                    line = line.rstrip()
                    if line:
                        log.debug(f"[parser] {line}")
            threading.Thread(target=_forward_stderr, daemon=True).start()

            # Read JSON frames from parser stdout
            for raw_line in proc.stdout:
                if not self._running:
                    break
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    frame = json.loads(raw_line)
                except json.JSONDecodeError:
                    self.stats["parse_errors"] += 1
                    log.debug(f"JSON parse error: {raw_line[:80]}")
                    continue

                with self._lock:
                    self.window.append(frame)
                self._frame_count += 1
                self.stats["frames"] += 1

                # Feed debug dashboard
                if self._debug_state is not None:
                    self._debug_state.update_frame(frame)

            proc.wait()
            if proc.returncode and proc.returncode != 0:
                log.error(f"Parser exited with code {proc.returncode}")

        except Exception as e:
            log.error(f"Reader thread error: {e}")
        finally:
            self._running = False

    # ── main loop ──────────────────────────────────────────────────────────────

    def run(self):
        self._running = True
        self._proc    = None

        log.info(
            f"Fall detector starting — "
            f"window={self.args.window} frames  "
            f"step={self.args.step} frames  "
            f"cooldown={self.args.cooldown}s"
        )

        # Start debug dashboard if requested
        if self._dashboard is not None:
            self._dashboard.start()
            log.info("Debug dashboard active — press 'q' to quit, 'c' to clear history")

        reader = threading.Thread(target=self._reader_thread, daemon=True)
        reader.start()

        last_infer_at  = 0
        # Warmup: skip inference for the first N frames so the window fills
        # with stable baseline data before we start making predictions.
        # At ~10fps, default warmup=48 = ~4.8 seconds.
        warmup_frames  = getattr(self.args, "warmup", 48)
        warmup_done    = False
        try:
            while self._running:
                current = self._frame_count

                if not warmup_done:
                    if current >= warmup_frames:
                        warmup_done = True
                        log.info(f"Warmup complete ({warmup_frames} frames) — inference active")
                    else:
                        time.sleep(0.01)
                        continue

                if (
                    len(self.window) >= self.args.window
                    and current - last_infer_at >= self.args.step
                ):
                    # Gate: skip inference if not enough points in window
                    # (empty room / no person → all-zero features → false fall)
                    with self._lock:
                        avg_pts = sum(
                            f.get("num_points_filt", 0)
                            for f in self.window
                        ) / max(1, len(self.window))
                    if avg_pts < self.args.min_points:
                        if self.args.verbose:
                            log.info(f"skip  avg_pts={avg_pts:.1f} < {self.args.min_points} (no person)")
                        time.sleep(0.01)
                        continue
                    last_infer_at = current
                    t0 = time.perf_counter()
                    prob, pred = self._infer()
                    elapsed_ms = (time.perf_counter() - t0) * 1000

                    self.stats["inferences"] += 1
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    alerted = False
                    if pred:
                        self.stats["falls_flagged"] += 1
                        alerted = self._maybe_alert(prob, ts)

                    self.logger.write(ts, pred, prob, alerted)

                    # Feed debug dashboard
                    if self._debug_state is not None:
                        self._debug_state.update_inference(prob, pred, alerted)

                    if self.args.verbose or pred:
                        tag = "FALL ⚠️ " if pred else "ok    "
                        log.info(
                            f"{tag} prob={prob:.3f}  "
                            f"frames={self.stats['frames']}  "
                            f"infer={elapsed_ms:.0f}ms  "
                            f"alerts={self.stats['alerts_sent']}"
                        )
                else:
                    time.sleep(0.01)

        except KeyboardInterrupt:
            log.info("Shutting down…")
        finally:
            self._running = False
            if self._dashboard is not None:
                self._dashboard.stop()
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
            if HAS_GPIO:
                try:
                    GPIO.output(27, GPIO.LOW)
                    GPIO.cleanup()
                except Exception:
                    pass
            log.info(
                f"Session summary — "
                f"frames={self.stats['frames']}  "
                f"inferences={self.stats['inferences']}  "
                f"falls={self.stats['falls_flagged']}  "
                f"alerts={self.stats['alerts_sent']}  "
                f"parse_errors={self.stats['parse_errors']}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description="Live fall detection — uses mmwave_run6.py as radar parser"
    )
    p.add_argument("--parser",       required=True,
                   help="Path to mmwave_run6.py")
    p.add_argument("--model",        required=True,
                   help="Path to best_model_pi_v3.pkl")
    p.add_argument("--cli-port",     default="/dev/ttyUSB0",
                   help="Radar CLI/config UART port  [default: /dev/ttyUSB0]")
    p.add_argument("--data-port",    default="/dev/ttyUSB1",
                   help="Radar data UART port        [default: /dev/ttyUSB1]")
    p.add_argument("--cfg-file",     default="config3.cfg",
                   help="Radar .cfg file             [default: config3.cfg]")
    p.add_argument("--window",       default=32,  type=int,
                   help="Sliding window size (frames) [default: 32]")
    p.add_argument("--step",         default=6,   type=int,
                   help="New frames between inferences [default: 6]")
    p.add_argument("--cooldown",     default=15.0, type=float,
                   help="Min seconds between alerts  [default: 15.0]")
    p.add_argument("--gotify-url",   default=None,
                   help="Gotify server base URL  e.g. http://192.168.1.10:8080")
    p.add_argument("--gotify-token", default=None,
                   help="Gotify app token")
    p.add_argument("--log",          default="fall_log.csv",
                   help="CSV log file path           [default: fall_log.csv]")
    p.add_argument("--verbose",      action="store_true",
                   help="Print every inference result")
    p.add_argument("--debug",        action="store_true",
                   help="Enable live terminal debug dashboard (requires debug_dashboard.py)")
    p.add_argument("--warmup",       default=48, type=int,
                   help="Frames to collect before first inference (~10fps so 48=~5s) [default: 48]")
    p.add_argument("--min-points",   default=5, type=float, dest="min_points",
                   help="Min avg points per frame in window to run inference [default: 5]")
    return p.parse_args()


def main():
    args = parse_args()

    # Sanity checks before starting
    if not os.path.exists(args.parser):
        log.error(f"Parser not found: {args.parser}")
        sys.exit(1)
    if not os.path.exists(args.model):
        log.error(f"Model not found: {args.model}")
        sys.exit(1)
    if not os.path.exists(args.cfg_file):
        log.error(f"Config file not found: {args.cfg_file}")
        sys.exit(1)
    if args.gotify_url and not args.gotify_token:
        log.warning("--gotify-url set but --gotify-token missing — alerts will not send")

    FallDetector(args).run()


if __name__ == "__main__":
    main()
