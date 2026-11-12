# 🏗️ TrussCAD Pro | Structural Design & FEA for Steel Trusses

An engineering CAD and structural calculation suite for steel trusses, specialized in inverted-V and pitched truss geometries using standard Peruvian/AISC cold-formed and hot-rolled structural steel profiles.

---

## ✨ Key Features

- **Structural Finite Element Solver (FEA):**
  - Direct stiffness method for 2D pin-jointed truss frameworks.
  - Automatic dead load, live load, and wind load distribution following Peruvian building codes (E.020, E.090).
  - Axial force calculation, tensile capacity, compression buckling verification, and slenderness checks ($KL/r$).
- **Peruvian Structural Steel Catalog:**
  - Standard tube sections (rectangular, square, circular), angles (L), channels (U), and double-angle chords.
- **Automated CAD Drafting (DXF Exporter):**
  - Generates detailed `.dxf` structural drawings with node annotations, chord dimensions, and member schedules compatible with AutoCAD, Civil 3D, and LibreCAD.
- **Engineering PDF Memory Generator:**
  - Automated generation of professional structural calculation reports with design checks, member utilization ratios, and code compliance verifications.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.9+**

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/jkulrtra12/truss-cad-pro.git
cd truss-cad-pro

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app_tijeral.py
```

---

## 🛠️ Tech Stack

- **Python** (Core application)
- **Tkinter / CustomTkinter** (Desktop GUI)
- **NumPy / SciPy** (Matrix structural analysis)
- **ezdxf** (AutoCAD DXF generation)
- **ReportLab** (Structural calculation memory generation)
