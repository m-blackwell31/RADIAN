# pi_deploy — Copy these 4 files to your Raspberry Pi

## Files
| File | Purpose |
|------|---------|
| `fall_detector_v2.py` | Live inference daemon — run this on the Pi |
| `mmwave_run6.py` | Radar parser — launched automatically by fall_detector_v2.py |
| `best_model_pi_v3.pkl` | Trained ML model (ExtraTrees, 86% accuracy, ~85ms on Pi 3B+) |
| `config3.cfg` | IWR6843 radar configuration |

## Copy to Pi
```bash
ssh pi@<YOUR_PI_IP> "mkdir -p ~/fall_detector"
scp fall_detector_v2.py   pi@<YOUR_PI_IP>:~/fall_detector/
scp mmwave_run6.py         pi@<YOUR_PI_IP>:~/fall_detector/
scp best_model_pi_v3.pkl   pi@<YOUR_PI_IP>:~/fall_detector/
scp config3.cfg            pi@<YOUR_PI_IP>:~/fall_detector/
```

## Install dependencies on Pi
```bash
pip3 install "scikit-learn==1.8.0" "numpy==2.4.2" "joblib==1.5.3" "pandas==3.0.1" pyserial requests
```

## Run
```bash
python3 fall_detector_v2.py \
  --parser     mmwave_run6.py \
  --model      best_model_pi_v3.pkl \
  --cli-port   /dev/ttyUSB0 \
  --data-port  /dev/ttyUSB1 \
  --cfg-file   config3.cfg \
  --gotify-url   http://YOUR_SERVER:8080 \
  --gotify-token YOUR_TOKEN \
  --verbose
```

See RADIAN_Deployment_Guide.pdf for full step-by-step instructions.
