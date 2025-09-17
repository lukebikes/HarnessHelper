from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QGridLayout, QMessageBox, QComboBox, QFrame
)
from PyQt6 import QtGui
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
import sys
import json
import math
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import itertools

plt.ion()


class HarnessCalculator(QWidget):
    def __init__(self):
        super().__init__()

        # Load wires.json from same folder as this script
        try:
            base = Path(__file__).parent
            with open(base / "wires.json", "r", encoding="utf-8") as f:
                self.wire_data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load wires.json: {e}")
            # Fallback minimal data so UI builds
            self.wire_data = {
                "core": {
                    "24 Gauge": {"area": 0.69, "core_radius": None},
                    "22 Gauge": {"area": 0.93, "core_radius": None}
                },
                "PVC": {
                    "24 Gauge": {"radius": 0.47, "amp_limit": 2},
                    "22 Gauge": {"radius": 0.54, "amp_limit": 3}
                }
            }

        # central core table (metal/conductor dimensions) — single source of truth
        self.core_table = self.wire_data.get("core", {})
        self.insulation_types = [k for k in self.wire_data.keys() if k != "core"]
        self.selected_insulation = self.insulation_types[0]
        self.input_widgets = []  # widgets added for wire inputs (for cleanup)
        self.inputs = {}  # QLineEdit per wire name
        self.initUI()

    def initUI(self):
        try:
            self.setWindowIcon(QtGui.QIcon('crimpino.png'))
        except Exception:
            pass

        self.setWindowTitle("Harness Diameter Calculator")
        self.setGeometry(100, 100, 700, 600)

        # Grid Layout
        grid = QGridLayout()
        self.grid = grid

        # Insulation dropdown
        row = 0
        grid.addWidget(QLabel("Insulation Type"), row, 0)
        self.insulation_dropdown = QComboBox()
        self.insulation_dropdown.addItems(self.insulation_types)
        self.insulation_dropdown.currentTextChanged.connect(self.on_insulation_change)
        grid.addWidget(self.insulation_dropdown, row, 1)
        row += 1

        # Wire inputs (populated from JSON)
        self.update_wire_inputs(start_row=row)

        # Custom wire row (placed after dynamic wire inputs)
        # update_wire_inputs sets self.next_row
        row = self.next_row
        self.custom_area_input = QLineEdit()
        self.custom_area_input.setValidator(QDoubleValidator(0.0, 999.99, 3))
        self.custom_count_input = QLineEdit()
        self.custom_count_input.setValidator(QIntValidator(0, 9999))
        grid.addWidget(QLabel("Custom (mm²)"), row, 0)
        grid.addWidget(self.custom_count_input, row, 1)
        grid.addWidget(QLabel("Wires"), row, 2)
        grid.addWidget(self.custom_area_input, row, 3)
        grid.addWidget(QLabel("mm² each"), row, 4)
        row += 1

        # Output Field
        self.result_label = QLabel("Harness Diameter:")
        grid.addWidget(self.result_label, row, 0, 1, 3)
        row += 1

        # Calculate Buttons
        self.calc_button = QPushButton("Calculate Harness Diameter")
        self.calc_button.clicked.connect(self.Calculate_diameter)
        grid.addWidget(self.calc_button, row, 0, 1, 2)
        row += 1

        self.bundle_button = QPushButton("Display Bundle Section")
        self.bundle_button.clicked.connect(self.DisplayBundleSection)
        grid.addWidget(self.bundle_button, row, 0, 1, 2)
        row += 1

        # Heat shrink input
        self.heatshrink_input = QLineEdit()
        self.heatshrink_input.setValidator(QDoubleValidator(0.0, 50.0, 3))
        self.heatshrink_input.setPlaceholderText("0 = none")
        grid.addWidget(QLabel("Heat shrink thickness (mm)"), row, 0)
        grid.addWidget(self.heatshrink_input, row, 1)
        row += 1

        # Layout Setup
        layout = QVBoxLayout()
        layout.addLayout(grid)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Second panel: Amp calc
        grid2 = QGridLayout()
        row2 = 0
        self.operation_dropdown = QComboBox()
        grid2.addWidget(QLabel("Wire Gauge"), row2, 0)
        # populate with available gauges — prefer core table keys
        gauges = list(self.core_table.keys()) if self.core_table else list(next(iter(self.wire_data.values())).keys())
        self.operation_dropdown.addItems(gauges)
        grid2.addWidget(self.operation_dropdown, row2, 1)

        row2 += 1
        self.operation_dropdown2 = QComboBox()
        grid2.addWidget(QLabel("Bundle loading percentage"), row2, 0)
        self.operation_dropdown2.addItems(["20", "40", "60", "80", "100"])
        grid2.addWidget(self.operation_dropdown2, row2, 1)

        row2 += 1
        self.input1 = QLineEdit()
        self.input1.setValidator(QIntValidator(0, 9999))
        grid2.addWidget(QLabel("Number of Wires in Bundle"), row2, 0)
        grid2.addWidget(self.input1, row2, 1)

        row2 += 1
        self.inputSF = QLineEdit()
        self.inputSF.setPlaceholderText("1")
        regex = QRegularExpression("^(?:[0-9][0-9]{0,1}(?:\\.\\d{1,2})?|99(?:\\.99)?)$")
        validator = QRegularExpressionValidator(regex)
        self.inputSF.setValidator(validator)
        grid2.addWidget(QLabel("Safety Factor"), row2, 0)
        grid2.addWidget(self.inputSF, row2, 1)

        row2 += 1
        self.result_label2 = QLabel("Current Limit: ")
        grid2.addWidget(self.result_label2, row2, 0, 1, 2)

        row2 += 1
        self.calculate_button = QPushButton("Calculate Current Limit")
        self.calculate_button.clicked.connect(self.Calculate_Amp)
        grid2.addWidget(self.calculate_button, row2, 0, 1, 2)

        layout.addLayout(grid2)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)

        # Third panel: Voltage drop
        grid3 = QGridLayout()
        row3 = 0
        self.operation_dropdown3 = QComboBox()
        grid3.addWidget(QLabel("Wire Gauge"), row3, 0)
        self.operation_dropdown3.addItems(gauges)
        grid3.addWidget(self.operation_dropdown3, row3, 1)

        row3 += 1
        label = QLabel("Current (A):")
        self.input_curr = QLineEdit()
        self.input_curr.setValidator(QIntValidator(0, 999))
        grid3.addWidget(label, row3, 0)
        grid3.addWidget(self.input_curr, row3, 1)

        row3 += 1
        label = QLabel("Length (m):")
        self.input_lenght = QLineEdit()
        self.input_lenght.setValidator(QDoubleValidator(0.0, 9999.0, 3))
        grid3.addWidget(label, row3, 0)
        grid3.addWidget(self.input_lenght, row3, 1)

        row3 += 1
        self.operation_dropdown4 = QComboBox()
        self.operation_dropdown4.addItems(["Cu", "Ag", "CuS"])
        grid3.addWidget(QLabel("Material"), row3, 0)
        grid3.addWidget(self.operation_dropdown4, row3, 1)

        row3 += 1
        self.result_label3 = QLabel("Voltage Drop: ")
        grid3.addWidget(self.result_label3, row3, 0, 1, 2)

        row3 += 1
        self.calc_drop_button = QPushButton("Calculate Voltage Drop")
        self.calc_drop_button.clicked.connect(self.Calculate_drop)
        grid3.addWidget(self.calc_drop_button, row3, 0, 1, 2)

        layout.addLayout(grid3)

        # material resistivity
        self.material_resistance = {"Cu": 0.00000172, "Ag": 0.00000159, "CuS": 0.00000159}

        self.setLayout(layout)

    def update_wire_inputs(self, start_row: int = 1):
        # Remove old widgets
        for w in self.input_widgets:
            try:
                self.grid.removeWidget(w)
            except Exception:
                pass
            try:
                w.deleteLater()
            except Exception:
                pass
        self.input_widgets.clear()
        self.inputs.clear()

        row = start_row
        # Build inputs from selected insulation set
        # input list should reflect gauges from core table when present
        wires = list(self.core_table.keys()) if self.core_table else list(self.wire_data.get(self.selected_insulation, {}).keys())
        if not wires:
            wires = ["(no wire data)"]

        for wire in wires:
            label = QLabel(wire)
            input_field = QLineEdit()
            input_field.setValidator(QIntValidator(0, 9999))
            wires_label = QLabel("Wires")
            self.inputs[wire] = input_field
            self.grid.addWidget(label, row, 0)
            self.grid.addWidget(input_field, row, 1)
            self.grid.addWidget(wires_label, row, 2)
            # store all created widgets so they are removed on next refresh
            self.input_widgets.extend([label, input_field, wires_label])
            row += 1

        self.next_row = row

    def on_insulation_change(self, text):
        self.selected_insulation = text
        # update gauge dropdowns to reflect available gauges (optional)
        gauges = list(self.wire_data.get(text, {}).keys())
        if gauges:
            # update operation_dropdowns without triggering signals
            self.operation_dropdown.clear()
            self.operation_dropdown.addItems(gauges)
            self.operation_dropdown3.clear()
            self.operation_dropdown3.addItems(gauges)
        self.update_wire_inputs(start_row=1)

    def Calculate_diameter(self):
        total_area = 0.0
        for wire, edit in self.inputs.items():
            txt = edit.text().strip()
            if not txt:
                continue
            try:
                count = int(txt)
                if count < 0:
                    raise ValueError
                # prefer perimeter/insulation area if explicitly provided, otherwise use core conductor area from core table
                ins_entry = self.wire_data.get(self.selected_insulation, {}).get(wire, {})
                core_entry = self.core_table.get(wire, {})
                area = float(ins_entry.get("area", core_entry.get("area", 0.0)))
                total_area += count * area
            except Exception:
                QMessageBox.warning(self, "Input Error", f"Invalid input for {wire}")
                return

        # custom wires
        custom_count = self.custom_count_input.text().strip()
        custom_area = self.custom_area_input.text().strip()
        if custom_count and custom_area:
            try:
                cc = int(custom_count)
                ca = float(custom_area)
                if cc < 0 or ca <= 0:
                    raise ValueError
                total_area += cc * ca
            except Exception:
                QMessageBox.warning(self, "Input Error", "Invalid custom wire values")
                return

        if total_area <= 0:
            self.result_label.setText("Harness Diameter: 0.00 mm")
            return

        diameter = 1.3 * math.sqrt(total_area)
        self.result_label.setText(f"Harness Diameter: {diameter:.2f} mm")

    def DisplayBundleSection(self):
        # gather wire tuples: (insulation_outer_radius_mm, core_area_mm2)
        wire_entries = []
        total_wires = 0
        for wire, edit in self.inputs.items():
            txt = edit.text().strip()
            if not txt:
                continue
            try:
                count = int(txt)
                if count < 0:
                    raise ValueError
                # outer radius (insulation) comes from selected insulation set
                ins_entry = self.wire_data.get(self.selected_insulation, {}).get(wire, {})
                r_outer = float(ins_entry.get("radius", 0.0))
                # core (metal) area comes from single core table (preferred)
                core_entry = self.core_table.get(wire, {})
                if "core_area" in core_entry:
                    core_area = float(core_entry["core_area"])
                elif "area" in core_entry:
                    core_area = float(core_entry["area"])
                else:
                    # fallback to any area present in insulation entry (legacy)
                    core_area = float(ins_entry.get("area", max(0.0001, math.pi * (r_outer * 0.5) ** 2)))
                total_wires += count
                for _ in range(count):
                    wire_entries.append((r_outer, core_area, wire))
            except Exception:
                QMessageBox.warning(self, "Input Error", f"Invalid input for {wire}")
                return

        # custom wires: assume provided area is core area; outer radius = core radius (no insulation)
        custom_count = self.custom_count_input.text().strip()
        custom_area = self.custom_area_input.text().strip()
        if custom_count and custom_area:
            try:
                cc = int(custom_count)
                ca = float(custom_area)
                if cc < 0 or ca <= 0:
                    raise ValueError
                core_radius = math.sqrt(ca / math.pi)
                total_wires += cc
                for _ in range(cc):
                    wire_entries.append((core_radius, ca, "Custom"))
            except Exception:
                QMessageBox.warning(self, "Input Error", "Invalid custom wire values")
                return

        if total_wires < 3:
            QMessageBox.warning(self, "Input Error", "Please enter at least 3 wires to display a bundle")
            return

        # sort by outer radius descending for better packing
        wire_entries.sort(key=lambda t: t[0], reverse=True)
        radii = [entry[0] for entry in wire_entries]  # outer radii
        core_areas = [entry[1] for entry in wire_entries]
        labels = [entry[2] for entry in wire_entries]

        # Pratt-style placement:
        positions = []  # list of (x,y,outer_r, core_area, label)
        # place first at origin
        positions.append((0.0, 0.0, radii[0], core_areas[0], labels[0]))

        def overlaps_any(x, y, r):
            for (px, py, pr, *_ ) in positions:
                if (x - px) ** 2 + (y - py) ** 2 < (r + pr - 1e-8) ** 2:
                    return True
            return False

        # helper: intersection points of two circles (centers c1,c2 radii R1,R2)
        def circle_intersections(c1, R1, c2, R2):
            (x1, y1) = c1
            (x2, y2) = c2
            dx = x2 - x1
            dy = y2 - y1
            d2 = dx * dx + dy * dy
            if d2 == 0:
                return []  # concentric
            d = math.sqrt(d2)
            # no solutions
            if d > (R1 + R2) + 1e-8 or d < abs(R1 - R2) - 1e-8:
                return []
            # two circle intersection
            a = (R1 * R1 - R2 * R2 + d * d) / (2 * d)
            h2 = max(0.0, R1 * R1 - a * a)
            xm = x1 + a * dx / d
            ym = y1 + a * dy / d
            if h2 == 0:
                return [(xm, ym)]
            h = math.sqrt(h2)
            rx = -dy * (h / d)
            ry = dx * (h / d)
            p1 = (xm + rx, ym + ry)
            p2 = (xm - rx, ym - ry)
            return [p1, p2]

        # place remaining with Pratt-like candidate generation (tangent to pairs + angle probes)
        for idx in range(1, len(radii)):
            r_new = radii[idx]
            core_area_new = core_areas[idx]
            label_new = labels[idx]
            candidates = []

            # 1) positions tangent to every placed circle at many angles (single circle probes)
            for (px, py, pr, *_ ) in positions:
                # sample angles for candidate tangency points (coarse)
                for theta in np.linspace(0, 2 * math.pi, 36, endpoint=False):
                    x = px + (pr + r_new) * math.cos(theta)
                    y = py + (pr + r_new) * math.sin(theta)
                    candidates.append((x, y))

            # 2) positions tangent to pairs of existing circles (intersection of circles of R = pr + r_new)
            for (i, a), (j, b) in itertools.combinations(enumerate(positions), 2):
                (x1, y1, r1, *_) = a
                (x2, y2, r2, *_) = b
                inters = circle_intersections((x1, y1), r1 + r_new, (x2, y2), r2 + r_new)
                for pt in inters:
                    candidates.append(pt)

            # evaluate candidates: sort by distance to origin (prefer compact)
            def cand_key(pt):
                return math.hypot(pt[0], pt[1])

            placed = False
            # remove duplicates and sort
            unique_candidates = []
            seen = set()
            for c in sorted(candidates, key=cand_key):
                key = (round(c[0], 6), round(c[1], 6))
                if key in seen:
                    continue
                seen.add(key)
                unique_candidates.append(c)

            for (x, y) in unique_candidates:
                if not overlaps_any(x, y, r_new):
                    positions.append((x, y, r_new, core_area_new, label_new))
                    placed = True
                    break

            if not placed:
                # fallback: spiral search outward
                R0 = 0.0
                maxR = max(10.0, sum(radii) * 1.5)
                for R in np.linspace(0, maxR, 800):
                    for theta in np.linspace(0, 2 * math.pi, max(24, int(6 * (R + 1)))):
                        x = R * math.cos(theta)
                        y = R * math.sin(theta)
                        if not overlaps_any(x, y, r_new):
                            positions.append((x, y, r_new, core_area_new, label_new))
                            placed = True
                            break
                    if placed:
                        break
                if not placed:
                    # place far on +x
                    x = maxR + r_new
                    y = 0.0
                    positions.append((x, y, r_new, core_area_new, label_new))

        # compute bundle outer radius
        bundle_outer = 0.0
        for x, y, r, *_ in positions:
            dist = math.hypot(x, y) + r
            if dist > bundle_outer:
                bundle_outer = dist

        # heatshrink thickness (mm)
        hs_text = self.heatshrink_input.text().strip()
        hs_thickness = 0.0
        try:
            if hs_text:
                hs_thickness = float(hs_text)
                if hs_thickness < 0:
                    hs_thickness = 0.0
        except Exception:
            hs_thickness = 0.0

        # plotting
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_aspect('equal')

        # draw outer heat shrink ring first (as faint fill)
        if hs_thickness > 0:
            outer_hs = bundle_outer + hs_thickness
            hs_patch = patches.Circle((0, 0), radius=outer_hs, edgecolor='red', facecolor=(1, 0.8, 0.8, 0.3), linewidth=1.0)
            ax.add_patch(hs_patch)
            # inner boundary of heatshrink (bundle outer)
            hs_inner = patches.Circle((0, 0), radius=bundle_outer, edgecolor='red', facecolor='none', linestyle='--')
            ax.add_patch(hs_inner)

        # draw each wire: insulation outer (color A) and core (color B)
        # choose colors per label (to reflect different insulation/core types)
        insulation_colors = ['#66c2a5', '#8da0cb', '#fc8d62', '#a6d854', '#ffd92f']
        core_colors = ['#2b7a5b', '#2f4a8a', '#b04532', '#4a7a2a', '#b07a02']
        color_map = {}
        for pos in positions:
            _, _, _, _, label = pos
            if label not in color_map:
                idx = len(color_map) % len(insulation_colors)
                color_map[label] = (insulation_colors[idx], core_colors[idx])

        for x, y, r_outer, core_area, label in positions:
            # insulation outer
            ins_color, core_color = color_map[label]
            circ_ins = patches.Circle((x, y), radius=r_outer, edgecolor='k', facecolor=ins_color, linewidth=0.6, zorder=1)
            ax.add_patch(circ_ins)
            # core radius from area
            core_r = math.sqrt(core_area / math.pi)
            # ensure core is strictly smaller than outer for visibility
            if core_r >= r_outer:
                core_r = r_outer * 0.98
            circ_core = patches.Circle((x, y), radius=core_r, edgecolor='k', facecolor=core_color, linewidth=0.3, zorder=2)
            ax.add_patch(circ_core)

        # compute diameters and update UI label (include heat shrink)
        bundle_dia_no_hs = 2.0 * bundle_outer
        if hs_thickness > 0:
            bundle_dia_with_hs = 2.0 * (bundle_outer + hs_thickness)
            self.result_label.setText(f"Bundle Ø = {bundle_dia_no_hs:.2f} mm  |  with HS Ø = {bundle_dia_with_hs:.2f} mm")
        else:
            self.result_label.setText(f"Bundle Ø = {bundle_dia_no_hs:.2f} mm")

        # annotate on plot
        ax.set_title(f"Estimated Bundle Section — {total_wires} wires\nInsulation: {self.selected_insulation}", fontsize=12)
        margin = 0.12 * (bundle_outer + hs_thickness + 1.0)
        ax.text(0, bundle_outer + hs_thickness + margin * 0.2, f"Bundle Ø = {bundle_dia_no_hs:.2f} mm", ha='center', fontsize=10, color='black')
        if hs_thickness > 0:
            ax.text(0, -(bundle_outer + hs_thickness + margin * 0.1), f"With heatshrink Ø = {bundle_dia_with_hs:.2f} mm", ha='center', fontsize=9, color='red')

        ax.set_xlim(-bundle_outer - hs_thickness - margin, bundle_outer + hs_thickness + margin)
        ax.set_ylim(-bundle_outer - hs_thickness - margin, bundle_outer + hs_thickness + margin)
        ax.axis('off')
        plt.show()

    def Calculate_Amp(self):
        try:
            WireSize = self.operation_dropdown.currentText()
            NumWire = float(self.input1.text() or 0)
            PercLoad = self.operation_dropdown2.currentText()
            SafetyFactor = float(self.inputSF.text()) if self.inputSF.text() else 1.0

            if PercLoad == "20":
                CoeffLoad = 0.4566806 + 0.5809375 * math.exp(-0.06637023 * NumWire)
            elif PercLoad == "40":
                CoeffLoad = 0.3831531 + 0.674138 * math.exp(-0.09878993 * NumWire)
            elif PercLoad == "60":
                CoeffLoad = 0.3254571 + 0.7533654 * math.exp(-0.1164914 * NumWire)
            elif PercLoad == "80":
                CoeffLoad = 0.3005456 + 0.7738705 * math.exp(-0.1294528 * NumWire)
            elif PercLoad == "100":
                CoeffLoad = 0.2701568 + 0.8338723 * math.exp(-0.1363069 * NumWire)
            else:
                CoeffLoad = 1.0

            if SafetyFactor == 0:
                raise ValueError

            # amp_limit remains per-insulation (depends on insulation)
            amp_limit = float(self.wire_data.get(self.selected_insulation, {}).get(WireSize, {}).get("amp_limit",
                                       self.core_table.get(WireSize, {}).get("amp_limit", 0.0)))
            result = CoeffLoad * amp_limit / SafetyFactor
            self.result_label2.setText(f"Current Limit: {result:.2f} A")
        except Exception:
            self.result_label2.setText("Error: Invalid Input")

    def Calculate_drop(self):
        try:
            chosencurrent = float(self.input_curr.text() or 0)
            distance = float(self.input_lenght.text() or 0)
            resistivity = self.material_resistance.get(self.operation_dropdown4.currentText(), 0.00000172)
            # use core conductor area (single core table) for voltage drop calculation
            gauge = self.operation_dropdown3.currentText()
            core_entry = self.core_table.get(gauge, {})
            area_conductor_mm2 = float(core_entry.get("area", self.wire_data.get(self.selected_insulation, {}).get(gauge, {}).get("area", 0.0)))
            area_mm2 = 0.75 * area_conductor_mm2
            area_m2 = area_mm2 / 10000.0  # mm² to m²
            if area_m2 <= 0:
                raise ValueError
            drop = chosencurrent * distance * resistivity / area_m2
            self.result_label3.setText(f"Voltage Drop: {drop:.2f} V")
        except Exception:
            self.result_label3.setText("Error: Invalid Input")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HarnessCalculator()
    window.show()
    sys.exit(app.exec())
