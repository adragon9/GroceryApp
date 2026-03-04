from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QSizePolicy, QListView,
                             QCheckBox, QDialog, QTableView,
                             QAbstractItemView, QGridLayout, QScrollArea,
                             QHeaderView)
from PyQt6.QtCore import Qt, QStringListModel, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class IngredientSelector(QDialog):
    def __init__(self, parent=None, ingredient_list:list=[], tag_list:list=[], data_pack: dict|None=None):
        super().__init__(parent)
        self.setWindowTitle("Ingredient Selector")
        self.setModal(True)  # This is key for proper modal behavior
        self.setMinimumSize(1600,900)
        self.ingredients = [ingredient[1] for ingredient in ingredient_list]
        self.tag_list = [tag[1] for tag in tag_list]
        self.ingredients.sort()
        self.tag_list.sort()
        
        if data_pack is None:
            self.data_pack = {
                "ingredients":[],
                "tags":[]
            }
        else:
            self.data_pack = data_pack

        main_layout = QVBoxLayout(self)
        
        # Group 1
        group_1 = QHBoxLayout()
        # ingredient model set up
        self.ingredient_view_model = QStringListModel()
        for ingredient in self.ingredients:
            self.ingredient_view_model.insertRows(self.ingredient_view_model.rowCount(), 1)  # Insert one row at the end
            index = self.ingredient_view_model.index(self.ingredient_view_model.rowCount() - 1, 0)
            self.ingredient_view_model.setData(index, ingredient, Qt.ItemDataRole.DisplayRole)
            
        self.ingredient_view = QListView()
        self.ingredient_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.ingredient_view.setModel(self.ingredient_view_model)
        # Makes sure no accidental ingredients are added
        self.ingredient_view.clearSelection()
        self.ingredient_view.setCurrentIndex(QModelIndex())
        
        # Button Layout
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0,0,0,0)
        
        # Button to transfer
        transfer_button = QPushButton("Add >>")
        transfer_button.setFixedWidth(124)
        remove_button = QPushButton("<< Remove")
        remove_button.setFixedWidth(124)
        
        button_layout.addWidget(transfer_button, alignment=Qt.AlignmentFlag.AlignBottom)
        button_layout.addWidget(remove_button, alignment=Qt.AlignmentFlag.AlignTop)

        
        # Added ingredients list setup
        self.table_model = QStandardItemModel(0, 3)
        self.table_model.setHorizontalHeaderLabels(["Ingredient","Amount","Measurement Unit"])
        self.ingredient_table = QTableView()
        self.ingredient_table.setModel(self.table_model)
        self.ingredient_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ingredient_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # type: ignore
        self.ingredient_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.ingredient_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ingredient_table.setAlternatingRowColors(True)
       
        # Layout setup
        group_1.addWidget(self.ingredient_view)
        group_1.addLayout(button_layout)
        group_1.addWidget(self.ingredient_table)
        
        # Tags
        tag_scroll_area = QScrollArea()
        tag_scroll_area.setWidgetResizable(True)
        tag_container = QWidget()
        tag_layout = QGridLayout(tag_container)
        tag_scroll_area.setWidget(tag_container)
        self.checkboxes = []
        
        for x, tag in enumerate(self.tag_list):
            row = x // 5
            new_checkbox = QCheckBox(f"{tag}")
            tag_layout.addWidget(new_checkbox, row, x % 5)
            self.checkboxes.append(new_checkbox)

                
        # Apply button
        apply_button = QPushButton("Apply")
        
        # Connections
        transfer_button.clicked.connect(self.add_ingredient_to_list)
        remove_button.clicked.connect(self.remove_ingredient_from_list)
        apply_button.clicked.connect(self.apply)

        # Main layout
        main_layout.addLayout(group_1,3)
        main_layout.addWidget(tag_scroll_area,1)
        main_layout.addWidget(apply_button)
        
        # Late Calls
        self.init_with_data_pack()

    def save_results(self):
        self.ingredient_selections = []
        for checkbox in self.findChildren(QCheckBox):
            if checkbox.isChecked():
                self.ingredient_selections.append(checkbox.text())
                
    def add_ingredient_to_list(self):
        selection_index = self.ingredient_view.currentIndex()
        if selection_index.isValid():
            sel_text = self.ingredient_view_model.data(selection_index, Qt.ItemDataRole.DisplayRole)
            name = QStandardItem(sel_text)
            quant = QStandardItem("0")
            unit =  QStandardItem("Enter Measurement Unit")
            
            name.setFlags(name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            row = [name, quant, unit]
            
            self.table_model.appendRow(row)
            # Makes sure no accidental ingredients are added
            self.ingredient_view.clearSelection()
            self.ingredient_view.setCurrentIndex(QModelIndex())
        self.ingredient_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # type: ignore # Reappplies the stretch to the columns
            
    def remove_ingredient_from_list(self):
        selection_index = self.ingredient_table.currentIndex()
        if selection_index.isValid():
            self.table_model.removeRow(selection_index.row())
            # Makes sure no accidental ingredients are removed
            self.ingredient_table.clearSelection()
            self.ingredient_table.setCurrentIndex(QModelIndex())
        self.ingredient_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # type: ignore # Reappplies the stretch to the columns
        
    def apply(self):
        # Clear these to prep them for the correct data
        self.data_pack["ingredients"] = []
        self.data_pack["tags"] = []
        
        tag_data = {}
        for checkbox in self.checkboxes:
            tag_data[checkbox.text()] = checkbox.isChecked()
        # DEBUG print(tag_data)
        
        rows = self.table_model.rowCount()
        columns = self.table_model.columnCount()
        for row in range(rows):
            row_data = []
            ingredient_data = {}
            for col in range(columns):
                index = self.table_model.index(row, col)
                cell_text = self.table_model.data(index, Qt.ItemDataRole.DisplayRole) or ""
                row_data.append(cell_text)
            
            ingredient_data["ingredient"]=row_data[0]
            ingredient_data["quantity"]=row_data[1]
            ingredient_data["measurement_unit"]=row_data[2]
            self.data_pack["ingredients"].append(ingredient_data)

        for key in tag_data.keys():
            if tag_data[key] == True:
                self.data_pack["tags"].append(key)
        # DEBUG print(f"From 'apply' in popup window: {self.data_pack}")
        
        self.close()
                
    def init_with_data_pack(self):
        for checkbox in self.checkboxes:
            for tag in self.data_pack["tags"]:
                if checkbox.text() == tag:
                    checkbox.setChecked(True)
                    
        for ingredient in self.data_pack["ingredients"]:          
            row = [QStandardItem(ingredient["ingredient"]), QStandardItem(ingredient["quantity"]), QStandardItem(ingredient["measurement_unit"])]
            self.table_model.appendRow(row)
            self.ingredient_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # type: ignore # Reappplies the stretch to the columns
              
    def get_data(self):
        return self.data_pack
    
    def closeEvent(self, a0):
        super().closeEvent(a0)