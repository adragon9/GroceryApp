import sqlite3, json
import datetime as dt

class DBHandler():
    def __init__(self):
        DB_NAME = "GroceryApp.db"
        self.db = sqlite3.connect(DB_NAME)
        self.cursor = sqlite3.Cursor(self.db)
        self.ensure_tables()
        self.create_backup()
        try:
            # Clears blank entries on load
            self.cursor.execute("""DELETE FROM ingredients WHERE name = ? """,("",))
            self.db.commit()
            if self.cursor.rowcount == 0:
                            print("No such ingredient found!")
        except sqlite3.Error as e:
            print(f"Error at blank entry check: {e}")
            
        self.__verify_ingredient_ids()
        
    # Add
    def ensure_tables(self):
        self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recipes(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        meal_type TEXT NOT NULL,
                        notes TEXT,
                        ingredients TEXT,
                        tags TEXT
                        )
                            """)
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS ingredients(
                                id INTEGER PRIMARY KEY,
                                name TEXT NOT NULL UNIQUE
                            )
                            """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)
        
        self.db.commit()
        
    def add_recipe(self, recipe_data: dict):
        try:
            ingredient_string = json.dumps(recipe_data["ingredients"])
            tags = json.dumps(recipe_data["tags"])

            self.cursor.execute(
                "INSERT INTO recipes(name, meal_type, notes, ingredients, tags) VALUES (?,?,?,?,?)",
                (recipe_data["name"], recipe_data["mealType"], recipe_data["notes"],ingredient_string,tags)
            )
            self.db.commit()
        except sqlite3.IntegrityError as e:
            print(f"Failed due to {e}")
    
    def add_ingredients(self, names:list):            
        for name in names:
            try:                        
                self.cursor.execute(
                    "INSERT INTO ingredients(name) VALUES (?)",
                        (name,)
                    )
                self.db.commit()
                self.__verify_ingredient_ids()
            except sqlite3.IntegrityError as e:
                self.db.rollback()
                print(f"Failed due to {e}")
            except sqlite3.ProgrammingError as e:
                self.db.rollback()
                print(f"Failed due to {e}")
                
    def add_tags(self, names: list):
        """Add a batch of tags"""
        for name in names:
            try:
                self.cursor.execute(
                    "INSERT INTO tags(name) VALUES (?)",
                    (name,)
                )
                self.db.commit()
                self.__verify_tag_ids()
            except sqlite3.IntegrityError as e:
                self.db.rollback()
                print(f"Failed due to {e}")
            except sqlite3.ProgrammingError as e:
                self.db.rollback()
                print(f"Failed due to {e}")
                
    # Retrieval
    def retrieve_recipes(self):
        try:
            self.cursor.execute("SELECT * FROM recipes")
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            print(f"Recipe retrieval failed!\nReason: {e}")
            return []
    
    def retrieve_ingredients(self)->list|None:
        self.__verify_ingredient_ids()
        try:
            self.cursor.execute("SELECT * FROM ingredients")
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            print(e)
            
    def retrieve_tags(self):
        self.__verify_tag_ids()
        try:
            self.cursor.execute("SELECT * FROM tags")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Failed to retrieve tags: {e}")
            return []
        
    def fetch_entry_data(self, entry_name:str):
        try:
            self.cursor.execute("SELECT * FROM recipes WHERE name=?",(entry_name,))
            result = self.cursor.fetchone()
            self.db.commit()
            return result
        except Exception as e:
            print(e)
            return str(e)
    # Remove
    def remove_ingredient(self, ingredient_name):
        try:
            self.cursor.execute("""DELETE FROM ingredients WHERE name = ? """,(ingredient_name,))
            self.db.commit()
            self.__verify_ingredient_ids()
            if self.cursor.rowcount == 0:
                print("No such ingredient found!")
        except sqlite3.Error as e:
            print(f"Error at remove_ingredient definition: {e}")
            self.db.rollback()
            
    def remove_tag(self, tag_name):
        """Remove a tag by name"""
        try:
            self.cursor.execute("DELETE FROM tags WHERE name = ?", (tag_name,))
            self.db.commit()
            self.__verify_tag_ids()
            if self.cursor.rowcount == 0:
                print(f"No such tag found: {tag_name}")
        except sqlite3.Error as e:
            print(f"Failed to remove tag '{tag_name}': {e}")
            
    # Update
    def __verify_ingredient_ids(self):
        """
        Docstring for __verify_ingredient_ids
        
        :param self: Ensures that there are no gaps in the ingredient ids
        """
        self.cursor.execute("SELECT id FROM ingredients")
        ids = self.cursor.fetchall()
        for i, id in enumerate(ids):
            if i+1 != id[0]:
                self.cursor.execute(
                    "UPDATE ingredients SET id = ? WHERE id = ?",
                    (i+1, id[0])
                    )
        self.db.commit()
        
    def __verify_tag_ids(self):
        """
        Docstring for __verify_tag_ids
        
        :param self: Ensures that there are no gaps in the ingredient ids
        """
        self.cursor.execute("SELECT id FROM tags")
        ids = self.cursor.fetchall()
        for i, id in enumerate(ids):
            if i+1 != id[0]:
                self.cursor.execute(
                    "UPDATE ingredients SET id = ? WHERE id = ?",
                    (i+1, id[0])
                    )
        self.db.commit()

    def update_recipe(self, recipe_data: dict):
        ingredients = json.dumps(recipe_data["ingredients"])
        tags = json.dumps(recipe_data["tags"])
        with self.db:
            self.cursor.execute("UPDATE recipes SET name=?, meal_type=?, notes=?, ingredients=?, tags=? WHERE id=?",
                            (recipe_data["name"], recipe_data["mealType"], recipe_data["notes"], 
                             ingredients, tags, recipe_data["id"]))
            
    # Back up
    def create_backup(self):
        """        
        :param self:
        \nThis is pretty simple for now, I might add better backups in the future
        """
        try:
            file_path = f"GroceryApp_Backup-{dt.datetime.strftime(dt.datetime.now(),"%m-%d-%Y")}.db"
            dest_conn = sqlite3.connect(file_path)
            with self.db:
                self.db.backup(dest_conn)
            # DEBUG print("Backup success!")
        except Exception as e:
            print(f"Backup failed!\nReason:{e}")