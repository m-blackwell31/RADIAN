# RADIAN — Radar-Based Fall Detection System

## Overview

RADIAN is a human fall detection system developed by Team 60 for the Texas A&M University ECEN 403/404 Capstone Program. The system uses a mmWave radar sensor combined with machine learning algorithms to detect falls in real time and alert caregivers via a mobile app notification.

---

## Repository Structure

```
/RADIAN
├── fall_detector/        # ML model and fall detection algorithms (Python)
├── MobileApp/            # Flutter/Dart mobile app for caregiver alerts
├── RADIAN_Data/          # Radar data collection scripts and mmWave run files
├── RADIAN_Physical/      # PCB design (Altium), CAD enclosure, power system
├── RADIAN_Radar/         # Radar configuration files and sensor interface code
└── GoogleDrive/          # Project documentation, presentations, and reports
    ├── docs/             # FSR, ICD, ConOps, final report, validation plan
    ├── presentations/    # All 403 and 404 presentations
    ├── data/             # Demo videos, diagrams, ML documentation
    ├── physical/         # Power board validation, datasheets, solder inspection
    ├── wireless/         # Radar testing data (.ndjson files)
    └── logo/             # RADIAN branding assets
```

---

## System Description

RADIAN uses a Texas Instruments AWR6843ISK mmWave radar sensor mounted at an elevated position to monitor a room. Point cloud data is streamed over UART to a Raspberry Pi, where a trained ExtraTrees machine learning classifier determines in real time whether a fall has occurred. Upon detection, a buzzer (GPIO27) alerts locally and a push notification is sent to the caregiver's mobile app via Gotify.

### Key Components

| Component | Description |
|---|---|
| TI AWR6843ISK | mmWave radar sensor |
| Raspberry Pi | Main compute module |
| AP64501 | Synchronous buck converter |
| MP2615 | Li-ion battery charger IC |
| S-8252AAO | 2-cell battery protection IC |
| 2S2P 7,000 mAh LiPo | Battery pack (~3h 45m runtime) |
| GPIO27 Buzzer | Local fall alert |
| Flutter Mobile App | Caregiver notification app |

---

## Getting Started

### Running the Fall Detector

SSH into the Raspberry Pi and run:

```bash
timeout 15 python3 mmwave_run6.py
```

The fall detector runs automatically on boot as a systemd service.

### Mobile App

See the `/MobileApp` directory for setup and build instructions.

---

## Team

**Texas A&M University — ECEN 403/404 Capstone, Spring 2026**
Team 60 — RADIAN Fall Detection System

| Name | GitHub |
|---|---|
| Matthew Blackwell | m-blackwell31 |
| Wyatt Johnson | ANDYSALAD1 |
| Mitch Hoffman | hoffmanmitchell |
| wyattjohnson-a1ly | wyattjohnson-a1ly |

---

## Instructors & Access

This repository is shared with:
- `kjnowka`
- `pranav-d1993`
- `johnlusher`
- `skalafatis`
