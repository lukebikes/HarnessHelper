from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QGridLayout, QMessageBox
)
import sys
import math

class HarnessCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Harness Diameter Calculator")
        self.setGeometry(100, 100, 400, 300)

        # Grid Layout
        grid = QGridLayout()
        
        self.inputs = {}  # Dictionary to store input fields
        self.wire_sizes = {
            "24 Gauge": 0.6939,
            "22 Gauge": 0.9331,
            "20 Gauge": 1.2668,
            "18 Gauge": 1.8140,
            "16 Gauge": 2.3500,
            "14 Gauge": 3.664,
            "27500 Shielded 2 Wire 22ga": 10.080,
            "27500 Shielded 3 Wire 22ga": 11.241
        }

        # Create labels and input fields dynamically
        row = 0
        for wire, _ in self.wire_sizes.items():
            label = QLabel(wire)
            input_field = QLineEdit()
            self.inputs[wire] = input_field  # Store input field reference
            grid.addWidget(label, row, 0)
            grid.addWidget(input_field, row, 1)
            grid.addWidget(QLabel("Wires"), row, 2)
            row += 1

        # Calculate Button
        self.calc_button = QPushButton("Calculate Harness Diameter")
        self.calc_button.clicked.connect(self.calculate_diameter)

        # Output Field
        self.result_label = QLabel("Harness Diameter:")
        self.result_field = QLineEdit()
        self.result_field.setReadOnly(True)

        # Layout Setup
        layout = QVBoxLayout()
        layout.addLayout(grid)
        layout.addWidget(self.calc_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_field)
        
        self.setLayout(layout)

    def calculate_diameter(self):
        total_area = 0

        for wire, area in self.wire_sizes.items():
            value = self.inputs[wire].text().strip()
            if value:
                try:
                    num_wires = int(value)
                    if num_wires < 0:
                        raise ValueError
                    total_area += num_wires * area
                except ValueError:
                    QMessageBox.warning(self, "Input Error", f"Invalid input for {wire}. Please enter a valid number.")
                    return

        # Final diameter calculation
        if total_area > 0:
            diameter = 1.25 * math.sqrt(total_area)
            self.result_field.setText(f"{diameter:.2f} mm")
        else:
            self.result_field.setText("0.00 mm")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HarnessCalculator()
    window.show()
    sys.exit(app.exec())
