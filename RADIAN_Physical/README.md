# RADIAN — Physical Subsystem

## Overview

This directory contains all physical design files for the RADIAN fall detection system, including the enclosure, PCB mounting hardware, and battery/component layout. The physical subsystem houses the Raspberry Pi compute module, mmWave radar sensor, power electronics, and buzzer in a compact, wearable-friendly enclosure.

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

> **Note:** A mass properties discrepancy was identified during design review — verify final mass against the assembly drawing before fabrication.

---

## PCB Design

- Designed in **Altium Designer**
- Includes power regulation (buck converter), MP2615 battery charger, UART communication lines, and GPIO buzzer output (GPIO27)
- Battery: 2S2P 7,000 mAh LiPo pack (~3h 45m runtime under ~1,500 mA load)

### Key Components

| Component | Description |
|---|---|
| Raspberry Pi | Main compute module |
| mmWave Radar | Fall detection sensor |
| MP2615 | Battery charger IC |
| Buck Converter | Voltage regulation |
| Buzzer (GPIO27) | Fall alert output |

---

## Hardware Assembly Notes

1. Mount PCB using M2.5 standoffs in enclosure mounting holes
2. Route mmWave sensor flush with enclosure sensor window
3. Connect battery pack to MP2615 charger input
4. Verify buzzer polarity before soldering (GPIO27 active-high)
5. Run CPU stress test and UART comms validation before final enclosure close

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
