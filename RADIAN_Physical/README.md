# RADIAN — Physical Subsystem

## Overview

This directory contains all physical design files for the RADIAN fall detection system, including the enclosure, PCB mounting hardware, and battery/component layout. The physical subsystem houses the Raspberry Pi compute module, mmWave radar sensor, power electronics, and buzzer in a compact, mountable enclosure.

---

## Directory Structure

```
/physical
├── CAD/
│   ├── enclosure.SLDPRT         # SolidWorks enclosure part file
│   ├── enclosure.SLDASM         # SolidWorks assembly file
│   └── drawings/                # Exported engineering drawings (PDF)
├── PCB/
│   ├── RADIAN.PrjPcb            # Altium project file
│   ├── RADIAN.SchDoc            # Schematic
│   ├── RADIAN.PcbDoc            # Board layout
│   ├── BOM.xlsx                 # Bill of materials
│   └── Gerbers/                 # Fabrication output files
├── Assembly/
│   ├── assembly_drawing.pdf     # Component placement guide
│   └── photos/                  # Build photos
└── README.md
```

---

## Enclosure

- Designed in **SolidWorks**
- Houses the Raspberry Pi, mmWave sensor, battery pack, and power board
- Mounting features for PCB standoffs and sensor window cutout
- Export formats: `.SLDPRT`, `.SLDASM`, PDF drawings

---

## PCB Design

- Designed in **Altium Designer**
- Includes power regulation (buck converter), MP2615 battery charger, and S-8252 protection IC 
- Battery: 2S2P 7,000 mAh LiPo pack (~3h 45m runtime under ~1,500 mA load)

### Key Components

| Component | Description |
|---|---|
| MP2615 | Battery charger IC |
| AP64501SP-1 | Buck Converter |
| 2-8252 | Protection IC

---


## Tools Required

- SolidWorks 2022 or later (CAD files)
- Altium Designer (PCB files)
- Standard PCB assembly tools (soldering station, multimeter, calipers)

---

## Team

**Texas A&M University — ECEN 404 Capstone**  
RADIAN Fall Detection System  
Spring 2026
