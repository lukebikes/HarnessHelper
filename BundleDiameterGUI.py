from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QLineEdit, QVBoxLayout, QGridLayout, QMessageBox, QComboBox, QFrame
)
from PyQt6 import QtGui
import sys
import math

class HarnessCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('crimpino.png'))
        if sys.platform.startswith("win"):
            import ctypes
            myappid = "mycompany.myproduct.subproduct.version"  # Arbitrary unique ID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

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
            "12 Gauge": 4.7,     #added after
            "27500 Shielded 2 Wire 22ga": 10.080,
            "27500 Shielded 3 Wire 22ga": 11.241
        }

        self.wire_Alimit = {
            "24 Gauge": 2,
            "22 Gauge": 3,
            "20 Gauge": 5,
            "18 Gauge": 7,
            "16 Gauge": 10,
            "14 Gauge": 20,
            "12 Gauge": 30,    
        }

        # Create labels and input fields dynamically
        row = 0
        for wire, _ in self.wire_sizes.items():
            label = QLabel(wire)
            input_field = QLineEdit()
            input_field.setValidator(QtGui.QIntValidator(0, 9999))  # Only allow positive integers
            self.inputs[wire] = input_field  # Store input field reference
            grid.addWidget(label, row, 0)
            grid.addWidget(input_field, row, 1)
            grid.addWidget(QLabel("Wires"), row, 2)
            row += 1

        # Calculate Harness Button
        self.calc_button = QPushButton("Calculate Harness Diameter")
        self.calc_button.clicked.connect(self.calculate_diameter)
        grid.addWidget(self.calc_button, row, 0 , 1, 3)

        # Output Field
        self.result_label = QLabel("Harness Diameter:")
        grid.addWidget(self.result_label, row+1, 0, 1, 3)
         #layout.addWidget(self.result_label)
       # self.result_field = QLineEdit()
        #self.result_field.setReadOnly(True)

        # Layout Setup
        layout = QVBoxLayout()
        layout.addLayout(grid)
       # layout.addWidget(self.calc_button)
       # layout.addWidget(self.result_label)
          # layout.addWidget(self.result_field)

         # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

         # Dropdown menu
        grid2 = QGridLayout() #grid layout for second part
        self.operation_dropdown = QComboBox()
        grid2.addWidget(QLabel("Wire Gauge"), 0, 0)
        self.operation_dropdown.addItems(["24 Gauge", "22 Gauge", "20 Gauge", "18 Gauge", "16 Gauge", "14 Gauge", "12 Gauge"])
        grid2.addWidget(self.operation_dropdown, 0 , 1)


        # Dropdown menu2
        
        self.operation_dropdown2 = QComboBox()
        grid2.addWidget(QLabel("Bundle loading percentage"), 1, 0)
        self.operation_dropdown2.addItems(["20", "40", "60", "80", "100"])
        grid2.addWidget(self.operation_dropdown2, 1, 1)
    
        # Input boxes
       
        self.input1 = QLineEdit()
        self.input1.setValidator(QtGui.QIntValidator(0, 9999))
        grid2.addWidget(QLabel("Number of Wires in Bundle"), 2, 0)
        grid2.addWidget(self.input1, 2, 1)
        
       

        
        # Calculate2 button
        self.calculate_button = QPushButton("Calculate Current Limit")
        self.calculate_button.clicked.connect(self.calculate_Amp)
        grid2.addWidget(self.calculate_button, 3, 0, 1, 2)

        # Result display
        self.result_label2 = QLabel("Current Limit: ")
        grid2.addWidget(self.result_label2, 4, 0, 1, 2)
        layout.addLayout(grid2)

        
        self.setWindowTitle("HarnessHelper")
        self.setGeometry(100, 100, 300, 250)
        
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
            self.result_label.setText(f"Harness Diameter: {diameter:.2f} mm")
        else:
            self.result_label.setText("Harness Diameter: 0.00 mm")

    ##Second Part
    
   

    def calculate_Amp(self):
        try:
            WireSize = self.operation_dropdown.currentText()
            NumWire = float(self.input1.text())
            PercLoad = self.operation_dropdown2.currentText()
            

            if PercLoad == "20" :
                CoeffLoad = 0.4566806 + 0.5809375*math.exp(-0.06637023*NumWire)
            elif PercLoad == "40" :
                CoeffLoad = 0.3831531 + 0.674138*math.exp(-0.09878993*NumWire)
            elif PercLoad == "60" :
                CoeffLoad = 0.3254571 + 0.7533654*math.exp(-0.1164914*NumWire)
            elif PercLoad == "80" :    
                CoeffLoad = 0.3005456 + 0.7738705*math.exp(-0.1294528*NumWire)
            elif PercLoad == "100" :
                CoeffLoad = 0.2701568 + 0.8338723*math.exp(-0.1363069*NumWire)
            
            
            result = CoeffLoad*self.wire_Alimit[WireSize]
                  

            self.result_label2.setText(f"Current Limit: {result:.2f} A")

        except ValueError:
            self.result_label2.setText("Error: Invalid Input")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HarnessCalculator()
    window.show()
    sys.exit(app.exec())
