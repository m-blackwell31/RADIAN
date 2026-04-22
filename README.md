# RADIAN — Radar-Based Fall Detection System

## Overview

RADIAN is a human fall detection system developed for the Texas A&M University ECEN 403/404 Capstone Course. The system uses a mmWave radar sensor combined with machine learning algorithms to detect falls in real time and alert caregivers via a mobile app notification.

---

## Repository Structure

```
/RADIAN
├── fall_detector/        # ML models (.pkl), fall detector scripts, training code
├── MobileApp/            # Flutter/Dart app (Gotify alerts, fall log, login screen)
├── RADIAN_Data/          # mmWave data collection, CNN model, radar testing scripts
├── RADIAN_Physical/      # PCB design (Altium), CAD enclosure, power system docs
├── RADIAN_Radar/         # AWR6843ISK config (config3.cfg), mmwave_run6.py, requirements
└── GoogleDrive/          # Project documentation, presentations, and reports
    ├── docs/             # FSR, ICD, ConOps, final report, validation plan, budget
    ├── presentations/    # All 403 and 404 status update and demo presentations
    ├── data/             # Demo videos, pipeline diagrams, ML documentation
    ├── physical/         # Power board validation, datasheets, solder inspection photos
    ├── wireless/         # Raw radar testing data (.ndjson files) — falls and non-falls
    └── logo/             # RADIAN branding assets
```

---

## System Description

RADIAN uses a Texas Instruments AWR6843ISK mmWave radar sensor mounted at an elevated position to monitor a room. Point cloud data is streamed over UART to a Raspberry Pi, where a trained ExtraTrees machine learning classifier determines in real time whether a fall has occurred. Upon detection, a buzzer (GPIO27) alerts locally, and a push notification is sent to the caregiver's mobile app via Gotify.

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

## Team

**Texas A&M University — ECEN 403/404 Capstone, Spring 2026**
Team 60 — RADIAN

| Name | GitHub |
|---|---|
| Matthew Blackwell | m-blackwell31 |
| Wyatt Johnson | ANDYSALAD1 |
| Mitch Hoffman | hoffmanmitchell |

