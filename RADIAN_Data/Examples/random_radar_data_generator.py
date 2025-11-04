import json
import random
import time

def generate_dummy_frame(frame_num, max_points=5):
    num_points = random.randint(0, max_points)
    points = []

    for _ in range(num_points):
        point = {
            "x": round(random.uniform(-2, 2), 6),
            "y": round(random.uniform(-2, 2), 6),
            "z": round(random.uniform(-0.5, 1.5), 6),
            "v": round(random.uniform(-1, 1), 6)
        }
        points.append(point)

    frame = {
        "ts": time.time(),
        "frame": frame_num,
        "num_points": num_points,
        "points": points
    }
    return frame

# Example: generate 10 dummy frames
for i in range(10):
    frame_data = generate_dummy_frame(i)
    print(f"[FRAME {i}] points={frame_data['num_points']} (numDetectedObj):{frame_data['num_points']}")
    print(json.dumps(frame_data, indent=2))
    time.sleep(0.1)
