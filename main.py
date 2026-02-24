import sys, ast
from rapidfuzz import fuzz
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QLineEdit, QTextEdit, QSizePolicy, QSpacerItem, 
                             QComboBox, QListView, QCheckBox, QDialog, QMenu,
                             QMessageBox, QTableView, QAbstractItemView, QGridLayout,
                             QScrollArea, QHeaderView)
from PyQt6.QtCore import Qt, QStringListModel, QModelIndex, QSortFilterProxyModel
from PyQt6.QtGui import QAction, QStandardItemModel, QStandardItem
import DatabaseManager

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            # Init database manager
            self.database = DatabaseManager.DBHandler()
        except Exception as e:
            QMessageBox.critical(self,"Database Error", f"Database failed to initalize with error: {e}")
        
        # Main vars
        self.measurement_types = ["oz", "g", "lbs"]
        self.measurement_types.sort()
        self.refresh_recipes()
        self.search_results = []
        self.popup_data = {}
        try:
            self.ingredients_list = self.database.retrieve_ingredients()
        except Exception as e:
            QMessageBox.critical(self,"Database Error", f"Ingredients failed to load with error: {e}")
            self.ingredients_list = [] 
            
        try:
            self.tags_list = self.database.retrieve_tags()
        except Exception as e:
            QMessageBox.critical(self,"Database Error", f"Tags failed to load with error: {e}")
            self.tags_list = [] 
            
        # Various window settings
        self.setWindowTitle("Grocery Manager")
        self.setMinimumSize(800, 600)

        # Create a tab widget
        self.tabs = QTabWidget()
        
        # Add recipe tab
        self.recipe_tab()
        
        # Add recipe editor tab
        self.recipe_editor_tab()
        
        # Add Grocery list editor
        self.grocery_list_tab()

        # Add ingredients tab
        self.ingredient_list_tab()
        self.init_ingredients_display()
        
        # Add tags tab
        self.tag_list_tab()
        self.init_tags_display()
        
        self.tabs.currentChanged.connect(self.edit_tab_display_update)

        # Set the tab widget as the central widget of the main window
        self.setCentralWidget(self.tabs)
        
    # Tabs
    def recipe_tab(self):
        """
        :param self:\n
        This is the setup for the recipe creation tab
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
                
        spacer_width = 0
        spacer_height = 40
        
        # Edit group 1
        layout.addItem(QSpacerItem(spacer_width, spacer_height, QSizePolicy.Policy.Minimum)) # Spacing
        
        self.recipe_name_label = QLabel(f"Recipe Name: ")
        self.recipe_name_input = QLineEdit()  # Renamed for clarity
        self.recipe_name_input.setPlaceholderText(f"Enter the name of your recipe...")
    
        layout.addWidget(self.recipe_name_label)
        layout.addWidget(self.recipe_name_input)
        
        # Meal time selection
        meal_types = ["Breakfast","Lunch","Dinner","Dessert","Snack"]
        self.combo_meal_types = QComboBox()
        self.combo_meal_types.addItems(meal_types)
        
        layout.addItem(QSpacerItem(spacer_width, spacer_height, QSizePolicy.Policy.Minimum)) # Spacing
        layout.addWidget(QLabel("Select meal type:"))
        layout.addWidget(self.combo_meal_types)
        
        # Additional notes
        self.tedit_notes = QTextEdit()
        self.tedit_notes.setPlaceholderText("Enter cooking instructions here...")
        
        layout.addItem(QSpacerItem(spacer_width, spacer_height, QSizePolicy.Policy.Minimum)) # Spacing
        layout.addWidget(self.tedit_notes)
        
        # Spacer to force apps to the top of the screen
        layout.addItem(QSpacerItem(spacer_width, spacer_height*2, QSizePolicy.Policy.Minimum)) # Spacing
        
        self.edit = QPushButton("Edit Details")
        submit = QPushButton("Submit")
        
        layout.addWidget(self.edit)
        layout.addWidget(submit)
        
        # Connections
        self.edit.clicked.connect(self.recipe_edit_popup)
        submit.clicked.connect(self.recipe_tab_submit)
        
        self.tabs.addTab(tab, "Add Recipe")
    
    def ingredient_list_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Ingredient list view setup
        self.ingredients_model = QStringListModel()
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(self.ingredients_model)
        proxy_model.setDynamicSortFilter(True)
        self.ingredients_view = QListView()
        self.ingredients_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.ingredients_view.setModel(proxy_model)
        proxy_model.sort(0, Qt.SortOrder.AscendingOrder) # Sort list
        
        # Group 1 - Add ingredient group
        group_1 = QHBoxLayout()
        self.ingredient_edit = QLineEdit()
        self.ingredient_edit.setPlaceholderText("Enter an ingredient here...")
        ingredient_submit = QPushButton("Submit")
        
        # Save button
        ingredient_save = QPushButton("Save")
        
        # Policies
        self.ingredients_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Connections
        self.ingredient_edit.returnPressed.connect(self.update_ingredients_display)
        self.ingredients_view.customContextMenuRequested.connect(self.ingredients_context_menu)
        ingredient_submit.clicked.connect(self.update_ingredients_display)
        ingredient_save.clicked.connect(self.save_ingredients)
        
        # Layout
        layout.addWidget(self.ingredients_view)
        layout.addLayout(group_1)
        group_1.addWidget(self.ingredient_edit)
        group_1.addWidget(ingredient_submit)
        layout.addWidget(ingredient_save)
        
        self.tabs.addTab(tab, "Manage Ingredients")

    def tag_list_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tag view setup
        self.tags_model = QStringListModel()
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(self.tags_model)
        proxy_model.setDynamicSortFilter(True)
        self.tags_view = QListView()
        self.tags_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.tags_view.setModel(proxy_model)
        proxy_model.sort(0, Qt.SortOrder.AscendingOrder) # Sort tags
        
        # Group 1 - Add tag
        group_1 = QHBoxLayout()
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("Enter a tag here...")
        tag_submit = QPushButton("Submit")
        
        # Save button
        tag_save = QPushButton("Save")
        
        # Policies
        self.tags_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Connections
        self.tag_edit.returnPressed.connect(self.update_tags_display)
        self.tags_view.customContextMenuRequested.connect(self.tags_context_menu)
        tag_submit.clicked.connect(self.update_tags_display)
        tag_save.clicked.connect(self.save_tags)
        
        # Layout
        layout.addWidget(self.tags_view)
        layout.addLayout(group_1)
        group_1.addWidget(self.tag_edit)
        group_1.addWidget(tag_submit)
        layout.addWidget(tag_save)
        
        self.tabs.addTab(tab, "Manage Tags")

    def recipe_editor_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Button width for consistent buttons    
        fixed_btn_width = 128
        
        # Group 1 - Recipe Search
        group_1 = QHBoxLayout()        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search recipe...")
        self.keyword_check = QCheckBox("Keyword Search")
        self.keyword_check.setCheckState(Qt.CheckState.Checked) # I think this is the better mode so I am leaving it checked by default
        search_btn = QPushButton("Search")
        search_btn.setFixedWidth(fixed_btn_width)

        # Recipe viewer setup
        self.recipe_viewer_model = QStringListModel(self.recipe_names)
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(self.recipe_viewer_model)
        proxy_model.setDynamicSortFilter(True)
        self.recipe_viewer = QListView()
        self.recipe_viewer.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.recipe_viewer.setModel(proxy_model)
        proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        proxy_model.sort(0, Qt.SortOrder.AscendingOrder) # Sort recipes
        
        # Policies
        ## NONE ##
        
        # Connections
        self.recipe_viewer.doubleClicked.connect(self.open_recipe_details)
        search_btn.clicked.connect(self.edit_tab_search)
        self.search_input.returnPressed.connect(search_btn.click)
        
        # Layout
        layout.addLayout(group_1)
        group_1.addWidget(self.search_input)
        group_1.addWidget(search_btn)
        layout.addWidget(self.keyword_check, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.recipe_viewer)
        
        self.tabs.addTab(tab, "Edit Recipe")

    def grocery_list_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.tabs.addTab(tab, "Make Shopping List")

    # Add recipe tab functions
    def recipe_tab_submit(self):
        # Ensure all required fields are edited
        if not self.recipe_name_input.text():
            self.recipe_name_label.setText("Recipe Name:*")
            self.recipe_name_label.setStyleSheet("color:red;font-weight:bold")
            QMessageBox.information(self, "Info", "You have not entered a name, no changes were saved.")
        elif not self.popup_data:
            self.edit.setText("Edit Details*")
            self.edit.setStyleSheet("color:red;font-weight:bold")
            QMessageBox.information(self, "Info", "You have not entered any tags or ingredients, no changes were saved.")
        else:
            submission_data = {
                "name":self.recipe_name_input.text(),
                "mealType":self.combo_meal_types.currentText(),
                "notes":self.tedit_notes.toPlainText(),
                "ingredients":self.popup_data["ingredients"],
                "tags":self.popup_data["tags"]
                
            }
            try:
                self.database.add_recipe(submission_data)
                # Reset the widgets and recipe data
                self.recipe_name_input.clear()
                self.combo_meal_types.setCurrentIndex(0)
                self.tedit_notes.clear()
                self.popup_data.clear()
                # Reset button and lable format
                self.recipe_name_label.setText("Recipe Name:")
                self.recipe_name_label.setStyleSheet("color:white;font-weight:normal")
                self.edit.setText("Edit Details")
                self.edit.setStyleSheet("color:white;font-weight:normal")
                QMessageBox.information(self, "Success", "New recipe added!") # Let the user know everything worked
                self.refresh_recipes()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error has occured @recipe_tab_submit please note the following error:\n{e}")
                            
    def edit_tab_search(self):
        self.search_input.setReadOnly(True) # Disable the line edit while search is preformed.
        self.search_results.clear()
        input_text = self.search_input.text().strip()
        self.search_input.clear()
                   
        if input_text == "":
            # Should make it so if the user has nothing in the search it just returns the regular recipe list
            self.recipe_viewer_model.removeRows(0, self.recipe_viewer_model.rowCount())
            self.recipe_viewer_model.setStringList(self.recipe_names)
        else:
            match_threshold = 23 # How sensitive should the search be higher num is stricter
            score_saves = {}
            
            for recipe in self.recipe_names:
                comparison_score = fuzz.ratio(recipe, input_text)
                if self.keyword_check.checkState() == Qt.CheckState.Checked:
                    for word in recipe.split(" "):
                        sub_score = fuzz.ratio(word.lower().strip(), input_text.lower())
                        if  sub_score >= 80:
                            score_saves[recipe] = comparison_score
                            break
                else:
                    score_saves[recipe] = comparison_score
            # Final results processing        
            if self.keyword_check.checkState() == Qt.CheckState.Unchecked:
                self.search_results = [key for key in score_saves.keys() if score_saves[key] >= match_threshold]
            else:
                self.search_results = [key for key in score_saves.keys()]
                    
            self.search_results.sort() # Might not be needed 
            
            self.recipe_viewer_model.removeRows(0, self.recipe_viewer_model.rowCount())
            self.recipe_viewer_model.setStringList(self.search_results)
        
        self.search_input.setReadOnly(False) # Re-enable the line edit once search is complete.
        
    def edit_tab_display_update(self):
        # Reinitializes the recipe viewer to reflect new changes to the db
        if self.tabs.currentIndex() == 1:
            self.recipe_viewer_model = QStringListModel(self.recipe_names)
            proxy_model = QSortFilterProxyModel()
            proxy_model.setSourceModel(self.recipe_viewer_model)
            proxy_model.setDynamicSortFilter(True)
            self.recipe_viewer.setModel(proxy_model)
            proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            proxy_model.sort(0, Qt.SortOrder.AscendingOrder)
            
    def open_recipe_details(self):
        ###--CAUTION--######################################################################################################
        # This has a pretty glaring issue in that it requires the data to be in the exact format it is in now.             #
        # I am editing data by specific array indecies which basically means that if any index is changed this will break. #
        ####################################################################################################################
        # Gets the current selection from the recipe list view
        entry_name = self.recipe_viewer.currentIndex().data(Qt.ItemDataRole.DisplayRole)
        
        # Create a popup dialog
        popup = QDialog(self)
        popup.setWindowTitle(f"Recipe Details {entry_name}")
        popup.setModal(True)
        popup.resize(600, 400)  # Set appropriate size for the dialog
        layout = QVBoxLayout(popup)
        
        # Gets the data from the db 
        entry_data = self.database.fetch_entry_data(entry_name)
        
        # Creates a new editable datapack for the db entry
        self.edit_data_pack = {
            "id":"",
            "name":"",
            "mealType":"",
            "notes":"",
            "ingredients":[],
            "tags":[]
            }
        
        # Populates the editable data pack
        for i, item in enumerate(entry_data):
            try:
                item_check = ast.literal_eval(item) # Checks for list
                if type(item_check) == list:
                    if type(item_check[0]) == dict:
                        self.edit_data_pack["ingredients"] = item_check
                    else:
                        self.edit_data_pack["tags"] = item_check        
            except Exception as e:
                # This here is the problem child make sure ALL indecies are correct
                if i == 0:
                    self.edit_data_pack["id"] = item
                elif i == 1:
                    self.edit_data_pack["name"] = item
                elif i == 2:
                    self.edit_data_pack["mealType"] = item
                elif i == 3:
                    self.edit_data_pack["notes"] = item
                else:
                    QMessageBox.critical(self, "Error", f"An error has occured @open_recipe_details please note the following error:\n{e}")

        # Add line edit for name
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.edit_data_pack["name"])
        
        # Add combo box for meal type
        self.meal_combo = QComboBox()
        meal_types = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]
        self.meal_combo.addItems(meal_types)
        self.meal_combo.setCurrentText(self.edit_data_pack["mealType"])
        
        # Add text edit for notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setText(self.edit_data_pack["notes"])
        
        # Buttons
        edit_details = QPushButton("Detailed Edit")
        save_btn = QPushButton("Save")
        
        # Policies
        ## NONE ##
        
        #Connections
        save_btn.clicked.connect(self.save_edits)
        save_btn.clicked.connect(popup.close)
        edit_details.clicked.connect(self.detailed_edit)
        
        #Layout
        layout.addWidget(self.name_edit)
        layout.addWidget(self.meal_combo)
        layout.addWidget(self.notes_edit)
        layout.addWidget(edit_details, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        popup.exec()
  
    def detailed_edit(self):
        saveable_data = self.recipe_edit_popup(data_pack=self.edit_data_pack)
        if saveable_data is not None:
            self.database.update_recipe(saveable_data)
        
        self.refresh_recipes()
        
    def save_edits(self):
        # Edit the data pack edp is garbage shorthand for edit data pack
        edp = self.edit_data_pack
        edp["name"] = self.name_edit.text()
        edp["mealType"] = self.meal_combo.currentText()
        edp["notes"] = self.notes_edit.toPlainText()
        
        # Make sure the datapack is actually populated
        if self.edit_data_pack is not None:
            self.database.update_recipe(edp)

        self.refresh_recipes()
        
        # Update displays to reflect changes
        self.edit_tab_display_update()
        
    # Ingredients tab functions
    def init_ingredients_display(self):
        """
        Docstring for init_ingredients_display
        
        :param self: Initializes the ingredients display with data from the db
        """
        if self.ingredients_list is not None:
            valid_ingredients = [s for s in self.ingredients_list if s[1].strip()] # Filter out any empty or whitespace-only ingredients first
            valid_ingredients = [s[1] for s in valid_ingredients] # Converts from list of tuples to list of strings
            valid_ingredients.sort() # Sort the list
            
            if valid_ingredients:  # Only proceed if there are valid entries
                start_row = self.ingredients_model.rowCount()
                count = len(valid_ingredients)
                
                self.ingredients_model.insertRows(start_row, count)

                for i, ingredient in enumerate(valid_ingredients):
                    index = self.ingredients_model.index(start_row + i, 0)
                    self.ingredients_model.setData(index, ingredient, Qt.ItemDataRole.DisplayRole)
 
    def update_ingredients_display(self):
        """
        Docstring for update_ingredients_display
        
        :param self: Update the display for ingredients
        """
        ingredient_text = self.ingredient_edit.text().strip().lower()
        if not ingredient_text or ingredient_text in [self.ingredients_model.data(self.ingredients_model.index(row, 0)) for row in range(self.ingredients_model.rowCount())]:
            QMessageBox.warning(self, "Duplicate Entry", "Ingredient already exists!")
            return
        
        self.ingredients_model.insertRows(self.ingredients_model.rowCount(), 1)  # Insert one row at the end
        index = self.ingredients_model.index(self.ingredients_model.rowCount() - 1, 0)
        self.ingredients_model.setData(index, self.ingredient_edit.text(), Qt.ItemDataRole.DisplayRole)
        self.ingredient_edit.clear()
        
        self.save_ingredients() # Runs a save whenever the display is updated

    def save_ingredients(self):
        ingredients = [self.ingredients_model.data(self.ingredients_model.index(row, 0), Qt.ItemDataRole.DisplayRole) for row in range(self.ingredients_model.rowCount())]
        ingredients = [lower_ingredient.strip().lower() for lower_ingredient in ingredients]
        self.database.add_ingredients(ingredients)
        try:
            self.ingredients_list = self.database.retrieve_ingredients()
        except Exception as e:
            QMessageBox.critical(self,"Database Error", f"Ingredients failed to load with error: {e}")
            self.ingredients_list = []
    
    def ingredients_context_menu(self, position):
        cmenu = QMenu()
        del_action = QAction("Delete Entry", self)
        del_action.triggered.connect(self.remove_ingredient)
        cmenu.addAction(del_action)
        cmenu.exec(self.mapToGlobal(position))
        
    def remove_ingredient(self):
        """
        Docstring for remove_ingredient
        
        :param self: 
        Attached to the context menu for the ingredients tab.
        Used to remove the ingredients from the display AND database.
        """
        confirmed = self.get_confirmation()
        if confirmed:
            index = self.ingredients_view.currentIndex()
            if index.isValid():
                ingredient = self.ingredients_model.data(index, Qt.ItemDataRole.DisplayRole)
                self.database.remove_ingredient(ingredient)
                self.ingredients_model.removeRow(index.row())
                self.save_ingredients()
        else:
            return

    # Tags tab functions
    def init_tags_display(self):
        """
        Docstring for init_tags_display
        
        :param self: Initializes the tags display with data from the db
        """
        if self.tags_list is not None:
            valid_tags = [s for s in self.tags_list if s[1].strip()] # Filter out any empty or whitespace-only tags first
            valid_tags = [s[1] for s in valid_tags] # Converts from list of tuples to list of strings
            valid_tags.sort() # Sort the list
            
            if valid_tags:  # Only proceed if there are valid entries
                start_row = self.tags_model.rowCount()
                count = len(valid_tags)
                
                self.tags_model.insertRows(start_row, count)

                for i, tag in enumerate(valid_tags):
                    index = self.tags_model.index(start_row + i, 0)
                    self.tags_model.setData(index, tag, Qt.ItemDataRole.DisplayRole)
    
    def update_tags_display(self):
        """
        Docstring for update_tags_display
        
        :param self: Update the display for tags
        """
        tag_text = self.tag_edit.text().strip().lower()
        if not tag_text or tag_text in [self.tags_model.data(self.tags_model.index(row, 0)) for row in range(self.tags_model.rowCount())]:
            QMessageBox.warning(self, "Duplicate Entry", "Tag already exists!")
            return
        self.tags_model.insertRows(self.tags_model.rowCount(), 1)  # Insert one row at the end
        index = self.tags_model.index(self.tags_model.rowCount() - 1, 0)
        self.tags_model.setData(index, self.tag_edit.text(), Qt.ItemDataRole.DisplayRole)
        self.tag_edit.clear()
        
        self.save_tags() # Runs a save whenever the display is updated

    def save_tags(self):
        tags = [self.tags_model.data(self.tags_model.index(row, 0), Qt.ItemDataRole.DisplayRole) for row in range(self.tags_model.rowCount())]
        tags = [lower_tag.strip().lower() for lower_tag in tags]
        self.database.add_tags(tags)
        try:
            self.tags_list = self.database.retrieve_tags()
        except Exception as e:
            QMessageBox.critical(self,"Database Error", f"Tags failed to load with error: {e}")
            self.tags_list = []
        
    def tags_context_menu(self, position):
        cmenu = QMenu()
        del_action = QAction("Delete Entry", self)
        del_action.triggered.connect(self.remove_tag)
        cmenu.addAction(del_action)
        cmenu.exec(self.mapToGlobal(position))
        
    def remove_tag(self):
        """
        Docstring for remove_tag
        
        :param self: 
        Attached to the context menu for the tags tab.
        Used to remove the tags from the display AND database.
        """
        confirmed = self.get_confirmation()
        if confirmed:
            index = self.tags_view.currentIndex()
            if index.isValid():
                tag = self.tags_model.data(index, Qt.ItemDataRole.DisplayRole)
                self.database.remove_tag(tag)
                self.tags_model.removeRow(index.row())
                self.save_tags()
        else:
            return

    # Multi-tab functions
    def recipe_edit_popup(self,data_pack:dict|None=None):
        # DEBUG print(f"LOCATION 'recipe_edit_popup': {data_pack}")
        if not data_pack:
            if self.ingredients_list and self.tags_list:
                popup = IngredientSelector(ingredient_list=self.ingredients_list, tag_list=self.tags_list)
            else:
                popup = IngredientSelector()
        else:
            if self.ingredients_list and self.tags_list:
                popup = IngredientSelector(ingredient_list=self.ingredients_list, tag_list=self.tags_list, data_pack=data_pack)
            else:
                popup = IngredientSelector()
        
        popup.exec()
        self.popup_data = popup.get_data()
      
    def get_confirmation(self):
        reply = QMessageBox.question(
            None,
            'Confirmation',
            "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False
        
    def refresh_recipes(self):
        '''
        :param self:
        \nRefresh the recipe data from the database to reflect changes
        '''
        self.recipes = self.database.retrieve_recipes()
        if self.recipes:
            self.recipe_names = [name[1] for name in self.recipes]
            self.recipe_names.sort()
        else:
            self.recipe_names = []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_size = 16
    app.setStyleSheet(f"""
        QWidget {{
            font-size: {font_size}pt;
        }}
        QTabBar::tab {{
            font-size: {font_size*.75}pt;
        }}
    """)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
