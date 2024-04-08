import sqlite3

class Database:
    """     DATABASE MANAGER 1.0
    This is a small SQLite database manager, which presents some types of methods
    like CRUD operations and table viewer.

    DISCLAIMER: Are missing some security points in this code, which will be fixed later, 
    so, only use for personal applications.

    CREDITS:  Rafael(ARDN)
    """

    def __init__(self, name: str):
        self.connection = None
        self.cursor = None
        self.db_name = name
        self.create_server_connection()

    def create_server_connection(self):
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

    def close_server_connection(self):
        self.cursor.close() #type:ignore
        self.connection.close() #type:ignore

    def commit(self):
        self.connection.commit() #type:ignore
    
    def create_table(self, table_name: str, columns_headers: str):
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name}({columns_headers})") #type:ignore
        self.commit()


    def insert_data(self, table_name: str, values: str):
        self.cursor.execute(f"INSERT INTO {table_name} VALUES ({values})") #type:ignore
        self.commit()

    def insert_manydata(self, table_name: str, values: str):
        self.cursor.executemany(f"INSERT INTO {table_name} VALUES ()", values) #type:ignore
        self.commit()


    def read_data(self, data='*', table_name='', otherstmt=''):
        rows = self.cursor.execute(f'SELECT {data} FROM {table_name} {otherstmt}').fetchall() #type:ignore
        return rows
    
    def update_data(self, table_name: str, data: str, where: str):
        self.cursor.execute(f"UPDATE {table_name} SET {data} WHERE {where}") #type:ignore
        self.commit()

    def delete_data(self, table_name: str, where=''):
        if where == '':
            q = input('This will DELETE ALL DATA from your Table, Proceed? [Y/N] ').upper().strip()
            if q == 'Y':
                self.cursor.execute(f"DELETE FROM {table_name}") #type:ignore
                self.commit()
            return
        
        self.cursor.execute(f"DELETE FROM {table_name} WHERE {where}") #type:ignore
        self.commit()

    def manual_sqlstmt(self, stmt: str):
            self.cursor.execute(stmt) #type:ignore
            self.commit()

    def view_tables(self):
        res = self.cursor.execute("SELECT name FROM sqlite_master") #type:ignore
        print(res.fetchall())