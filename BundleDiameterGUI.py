from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QLineEdit, QVBoxLayout, QGridLayout, QMessageBox, QComboBox, QFrame
)
from PyQt6 import QtGui
from PyQt6.QtGui import (QIntValidator, QDoubleValidator, QRegularExpressionValidator)
from PyQt6.QtCore import QRegularExpression
import sys
import math
import packcircles as pc
import matplotlib.pyplot as plt
from matplotlib import colormaps
import Wires as wire_dm
import random
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

plt.ion()

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
        self.wire_sizes = {     #wires Area in mm^2
            "24 Gauge": 0.6939,
            "22 Gauge": 0.9331,
            "20 Gauge": 1.2668,
            "18 Gauge": 1.8140,
            "16 Gauge": 2.3500,
            "14 Gauge": 3.664,
            "12 Gauge": 4.7,     #added after
            "27500 Shielded 2 Wire 22ga": 10.080,
            "27500 Shielded 3 Wire 22ga": 11.241,
        }
        # Add custom wire row
        row = 0
        for wire, _ in self.wire_sizes.items():
            label = QLabel(wire)
            input_field = QLineEdit()
            input_field.setValidator(QIntValidator(0, 9999))  # Only allow positive integers
            self.inputs[wire] = input_field  # Store input field reference
            grid.addWidget(label, row, 0)
            grid.addWidget(input_field, row, 1)
            grid.addWidget(QLabel("Wires"), row, 2)
            row += 1

        # Custom wire row
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




        self.conductor_size = {
            "24 Gauge" : 0.2050,
            "22 Gauge" : 0.3250,
            "20 Gauge" : 0.5190,
            "18 Gauge" : 0.8230,
            "16 Gauge" : 1.3100,
            "14 Gauge" : 2.0800,
            "12 Gauge" : 3.3100,
        }



        self.wire_radius = {
            "27500 Shielded 3 Wire 22ga": 3.783/2,
            "27500 Shielded 2 Wire 22ga": 3.582/2,
            "12 Gauge": 2.446/2,
            "14 Gauge": 2.160/2,
            "16 Gauge": 1.730/2,
            "18 Gauge": 1.520/2,
            "20 Gauge": 1.270/2,
            "22 Gauge": 1.090/2,
            "24 Gauge": 0.940/2,
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

        self.material_resistance = {
            "Cu": 0.00000172,
            "Ag": 0.00000159,
            "CuS": 0.00000159,
        }

        # # Create labels and input fields dynamically
        # row = 0
        # for wire, _ in self.wire_sizes.items():
        #     label = QLabel(wire)
        #     input_field = QLineEdit()
        #     input_field.setValidator(QIntValidator(0, 9999))  # Only allow positive integers
        #     self.inputs[wire] = input_field  # Store input field reference
        #     grid.addWidget(label, row, 0)
        #     grid.addWidget(input_field, row, 1)
        #     grid.addWidget(QLabel("Wires"), row, 2)
        #     row += 1

        # # Output Field
        # self.result_label = QLabel("Harness Diameter:")
        # grid.addWidget(self.result_label, row, 0, 1, 3)

        row += 1
        # Calculate Harness Buttons
        self.calc_button = QPushButton("Calculate Harness Diameter")
        self.calc_button.clicked.connect(self.Calculate_diameter)
        grid.addWidget(self.calc_button, row, 0 , 1, 3)
        row += 1
        self.calc_button = QPushButton("Display Bundle Section")
        self.calc_button.clicked.connect(self.DisplayBundleSection)
        grid.addWidget(self.calc_button, row, 0 , 1, 3)
        row += 1

        
       

        # Layout Setup
        layout = QVBoxLayout()
        layout.addLayout(grid)
      

         # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

         # Dropdown menu1
        row2=0
        grid2 = QGridLayout() #grid layout for second part
        self.operation_dropdown = QComboBox()
        grid2.addWidget(QLabel("Wire Gauge"), 0, 0)
        self.operation_dropdown.addItems(["24 Gauge", "22 Gauge", "20 Gauge", "18 Gauge", "16 Gauge", "14 Gauge", "12 Gauge"])
        grid2.addWidget(self.operation_dropdown, row2 , 1)


        # Dropdown menu2
        row2 += 1
        self.operation_dropdown2 = QComboBox()
        grid2.addWidget(QLabel("Bundle loading percentage"), 1, 0)
        self.operation_dropdown2.addItems(["20", "40", "60", "80", "100"])
        grid2.addWidget(self.operation_dropdown2, row2, 1)
    
        # Input wire number boxes
        row2 += 1
        self.input1 = QLineEdit()
        self.input1.setValidator(QIntValidator(0, 9999))
        grid2.addWidget(QLabel("Number of Wires in Bundle"), row2 , 0)
        grid2.addWidget(self.input1, row2 , 1)

         # Input wire Safety Factor
        row2 += 1
        self.inputSF = QLineEdit()
        self.inputSF.setPlaceholderText("1")
        regex = QRegularExpression("^(?:[0-9][0-9]{0,1}(\.\d{1,2})?|99(\.99)?)$")
        validator = QRegularExpressionValidator(regex)
        self.inputSF.setValidator(validator)
        grid2.addWidget(QLabel("Safety Factor"), row2 , 0)
        grid2.addWidget(self.inputSF, row2, 1)
       
        # Result display
        row2 += 1
        self.result_label2 = QLabel("Current Limit: ")
        grid2.addWidget(self.result_label2, row2 , 0, 1, 2)
        layout.addLayout(grid2)

        # Calculate2 button
        row2 += 1
        self.calculate_button = QPushButton("Calculate Current Limit")
        self.calculate_button.clicked.connect(self.Calculate_Amp)
        grid2.addWidget(self.calculate_button, row2 , 0, 1, 2)

        

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Dropdown menu3
        row3=0
        grid3 = QGridLayout() #grid layout for second part
        self.operation_dropdown3 = QComboBox()
        grid3.addWidget(QLabel("Wire Gauge"), 0, 0)
        self.operation_dropdown3.addItems(["24 Gauge", "22 Gauge", "20 Gauge", "18 Gauge", "16 Gauge", "14 Gauge", "12 Gauge"])
        grid3.addWidget(self.operation_dropdown3, row3 , 1)

        # Input boxes3
        row3 += 1
        label = QLabel("Current (A):")
        self.input_curr = QLineEdit()
        self.input_curr.setValidator(QIntValidator(0, 999))  # Only allow positive integers
        grid3.addWidget(label, row3, 0)
        grid3.addWidget(self.input_curr, row3, 1)

        # Input boxes3
        # row3 += 1
        # label = QLabel("Voltage (V):")
        # self.input_volt = QLineEdit()
        # self.input_volt.setValidator(QIntValidator(0, 999))  # Only allow positive integers
        # grid3.addWidget(label, row3, 0)
        # grid3.addWidget(self.input_volt, row3, 1)

         # Input boxes3
        row3 += 1
        label = QLabel("Lenght (m):")
        self.input_lenght = QLineEdit()
        self.input_lenght.setValidator(QIntValidator(0, 999))  # Only allow positive integers
        grid3.addWidget(label, row3, 0)
        grid3.addWidget(self.input_lenght, row3, 1)
       
        # Dropdown menu3
        row3 += 1
        self.operation_dropdown4 = QComboBox()
        grid3.addWidget(QLabel("Conductor Material"), row3, 0)
        self.operation_dropdown4.addItems(["Cu", "Ag", "CuS"])
        grid3.addWidget(self.operation_dropdown4, row3 , 1)



        # Result display3
        row3 += 1
        self.result_label3 = QLabel("Voltage Drop: ")
        grid3.addWidget(self.result_label3, row3 , 0, 1, 2)
        layout.addLayout(grid3)

        # Calculate button3
        row3 += 1
        self.calculate_button3 = QPushButton("Calculate Voltage Drop")
        self.calculate_button3.clicked.connect(self.Calculate_drop)
        grid3.addWidget(self.calculate_button3, row3 , 0, 1, 2)

        # # Result display3
        # row3 += 1
        # self.result_label3 = QLabel("Voltage Drop: ")
        # grid3.addWidget(self.result_label3, row3 , 0, 1, 2)
        # layout.addLayout(grid3)



        # Set layout
        self.setWindowTitle("HarnessHelper")
        self.setGeometry(1000, 100, 300, 300)
        
        self.setLayout(layout)

    # def format_decimal(self):
    #     """Ensures the input always displays one decimal place correctly."""
    #     text = self.inputSF.text().strip()

    #     if text:  # If the field is not empty
    #         try:
    #             # Preserve leading zero for numbers like 0.2
    #             if "." in text:
    #                 num = float(text)
    #                 formatted_text = "{:.1f}".format(num)  # Format to one decimal place
    #             else:
    #                 num = int(text)
    #                 formatted_text = f"{num}.0"  # Ensure decimal formatting

    #             self.inputSF.setText(formatted_text)  # Update text field
    #         except ValueError:
    #             pass  # Ignore invalid input

    def Calculate_diameter(self):
        total_area = 0
        print(wire_dm.TXL_diameters)
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
                
        # Handle custom wire
        custom_count = self.custom_count_input.text().strip()
        custom_area = self.custom_area_input.text().strip()
        if custom_count and custom_area:
            try:
                num_wires = int(custom_count)
                area = float(custom_area)
                if num_wires < 0 or area <= 0:
                    raise ValueError
                total_area += num_wires * area
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Invalid input for custom wire. Please enter valid numbers.")
                return

        # Final diameter calculation
        if total_area > 0:
            diameter = 1.3 * math.sqrt(total_area)
            self.result_label.setText(f"Harness Diameter: {diameter:.2f} mm")
        else:
            self.result_label.setText("Harness Diameter: 0.00 mm")

    def DisplayBundleSection(self):
        radii=[]
        totnum_wires = 0
        for wire, radio in self.wire_radius.items():
            value = self.inputs[wire].text().strip()
            if value:
                try:
                    num_wires = int(value)
                    if num_wires < 0:
                        raise ValueError
                    totnum_wires += num_wires
                    for times in range(num_wires):
                        radii.append(radio)
                except ValueError:
                    QMessageBox.warning(self, "Input Error", f"Invalid input for {wire}. Please enter a valid number.")
                    return
        # --- Add custom wires to bundle display ---
        custom_count = self.custom_count_input.text().strip()
        custom_area = self.custom_area_input.text().strip()
        if custom_count and custom_area:
            try:
                num_wires = int(custom_count)
                area = float(custom_area)
                if num_wires < 0 or area <= 0:
                    raise ValueError
                # Area = pi * r^2 => r = sqrt(area / pi)
                custom_radius = math.sqrt(area / math.pi)
                totnum_wires += num_wires
                for _ in range(num_wires):
                    radii.append(custom_radius)
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Invalid input for custom wire. Please enter valid numbers.")
                return
        # --- end custom wires ---        
        






        if totnum_wires < 3:
            QMessageBox.warning(self, "Input Error", f"Please enter at least 3 wires")
            return
        else: 
            #print(radii)
            fig = plt.figure()
            ax = plt.subplot()
            cmap = colormaps['coolwarm_r']
            circles = pc.pack(radii)
            circle_data = [(x, y, r) for (x, y, r) in circles]
            circles = pc.pack(radii)
            maxradius = 0
            for (x,y,rado) in circles:
                patch = plt.Circle(
                    (x,y),
                    rado,
                    color=cmap(rado/max(radii)),
                    alpha=1
                )
                bundleradius = math.sqrt(x**2 + y**2) + rado
                if bundleradius > maxradius:
                    maxradius = bundleradius
                ax.add_patch(patch)
                patch2 = plt.Circle(
                    (x,y),
                    rado/2,
                    color= 'brown',
                    alpha=1
                )
                ax.add_patch(patch2)

            termow=1
            
            cx, cy, cr = self.pratt_min_enclosing_circle(circle_data)
            patch3 = plt.Circle(
                (cx, cy),
                cr,
                color='black',
                fill = False
            )
            ax.add_patch(patch3)  

            patch4 = plt.Circle(
                (cx, cy),
                cr+termow,
                color='black',
                fill = False
            )
            ax.add_patch(patch4)  




            fig.set_figheight(7)
            fig.set_figwidth(7)
            ax.set(xlim=(-15, 15), ylim=(-15, 15))
            plt.gca().set_aspect('equal')
            plt.axis('off')
            plt.show()
            self.result_label.setText(f"Harness Diameter: {2*(cr+termow):.2f} mm")
        

   

    def Calculate_Amp(self):
        try:
            
            WireSize = self.operation_dropdown.currentText()
            NumWire = float(self.input1.text())
            PercLoad = self.operation_dropdown2.currentText()
            SafetyFactor = float(self.inputSF.text()) if self.inputSF.text() else 1


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
            
            if SafetyFactor == 0:
                raise ValueError
            result = CoeffLoad*float(self.wire_Alimit[WireSize])/float(SafetyFactor)
            self.result_label2.setText(f"Current Limit: {result:.2f} A")

        except ValueError:
            self.result_label2.setText("Error: Invalid Input")


    def Calculate_drop(self):
        try:
            # voltage = float(self.input_volt.text())
            chosencurrent = float(self.input_curr.text())
            distance = float(self.input_lenght.text())
            resistivity = self.material_resistance[self.operation_dropdown4.currentText()]

            drop = chosencurrent * distance * resistivity / (self.wire_sizes[self.operation_dropdown3.currentText()]/1000)
            self.result_label3.setText(f"Voltage Drop: {drop:.2f} V")

        except ValueError:
            self.result_label3.setText("Error: Invalid Input")
    @staticmethod
    def dist(x1, y1, x2, y2):
         return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    @staticmethod
    def pratt_min_enclosing_circle(circles, tol=1e-6, max_iter=1500):
        if not circles:
            raise ValueError("No circles provided")
    
        # Initialize with the first circle's center and radius
        cx, cy, cr = circles[0]
    
        for _ in range(max_iter):
            violations = [(x, y, r) for x, y, r in circles if HarnessCalculator.dist(cx, cy, x, y) + r > cr]
            if not violations:
                break
        
        # Pick a random violating circle
            x, y, r = random.choice(violations)
            d = HarnessCalculator.dist(cx, cy, x, y)
        
        # Update center and radius
            new_cr = (d + r + cr) / 2
            ratio = (new_cr - cr) / d if d != 0 else 0
            cx += (x - cx) * ratio
            cy += (y - cy) * ratio
            cr = new_cr
    
        return cx, cy, cr

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HarnessCalculator()
    window.show()
    sys.exit(app.exec())
