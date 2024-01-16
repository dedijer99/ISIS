import pandas
import pyodbc

from data.learning_model import LearningModel

class DataBase:
    def __init__(self):
        database_con = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                                      'Server=DESKTOP-FR93L69\SQLEXPRESS;'
                                      'Database=load_forecast;'
                                      'Trusted_Connection=yes;')
        cursor = database_con.cursor()
        database_con.commit()
        cursor.close()
        database_con.close()

    def connect(self):
        return pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                                      'Server=DESKTOP-FR93L69\SQLEXPRESS;'
                                      'Database=load_forecast;'
                                      'Trusted_Connection=yes;')
        
    def clean_data_input(self):
        database_conn = self.connect()
        cursor = database_conn.cursor()
        
        cursor.execute('DELETE FROM dbo.TestSet WHERE 1=1')
        
        database_conn.commit()
        cursor.close()
        database_conn.close()

    def add_element(self, element: LearningModel, learning: bool):
        database_con = self.connect()
        cursor = database_con.cursor()

        table = ''
        if learning == False:
            table = 'TestSet'
        else:
            table = "LearningSet"

        sql = 'INSERT INTO dbo.'+ table +' (Year, Month, Day, Hour, Temp, Feelslike, Humidity, WindSpeed, CloudCover, WeeakDay, Daylight, Load) ' \
              'VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(
                element.year, element.month, element.day, element.hour, element.temp, element.feels_like, element.humidity, element.wind_speed, element.cloud_cover, element.week_day, element.daylight, element.load
              )
        cursor.execute(sql)
        database_con.commit()
        cursor.close()
        database_con.close()
        
    def insert_average_load_data(self, year_recorded, month_recorded, day_recorded, average_load, is_learning):
        def execute_insert_query(connection, query):
            with connection.cursor() as cursor:
                cursor.execute(query)
                connection.commit()

        def construct_sql(year, month, day, load, learning):
            table_suffix = 'Input' if not learning else ''
            table_name = f'AverageLoad{table_suffix}'
            return f'INSERT INTO dbo.{table_name} (Year, Month, Day, AvgLoad) VALUES ({year}, {month}, {day}, {load})'

        db_connection = self.connect()
        sql_query = construct_sql(year_recorded, month_recorded, day_recorded, average_load, is_learning)
        execute_insert_query(db_connection, sql_query)
        db_connection.close()

    def add_average_load(self, year, month, day, avg_load, learning):
        database_con = self.connect()
        cursor = database_con.cursor()

        input = ''
        if learning == False:
            input = 'Input'

        sql = 'INSERT INTO dbo.AverageLoad' + input + ' (Year, Month, Day, AvgLoad) ' \
              'VALUES ({}, {}, {}, {})'.format(
                year, month, day, avg_load
              )
        cursor.execute(sql)
        database_con.commit()
        cursor.close()
        database_con.close()

    def get_pandas_dataframe(self, yearFrom, monthFrom, dayFrom, yearTo, monthTo, dayTo, learningData):
        database_con = self.connect()
        cursor = database_con.cursor()
        
        date_from = (dayFrom, monthFrom, yearFrom)  # 1st January 2023
        date_to = (dayTo, monthTo, yearTo)   # 31st January 2023

        date_from_str = f"{date_from[2]}-{str(date_from[1]).zfill(2)}-{str(date_from[0]).zfill(2)}"
        date_to_str = f"{date_to[2]}-{str(date_to[1]).zfill(2)}-{str(date_to[0]).zfill(2)}"

        table = ''
        if learningData == False:
            table = 'TestSet'
        else:
            table = "LearningSet"        
        
        query = f"""
        SELECT *
        FROM dbo.{table}
        WHERE CAST(
                CAST([Year] AS VARCHAR(4)) + '-' + 
                RIGHT('0' + CAST([Month] AS VARCHAR(2)), 2) + '-' + 
                RIGHT('0' + CAST([Day] AS VARCHAR(2)), 2)
            AS DATETIME) 
            BETWEEN '{date_from_str}' AND '{date_to_str}'
        """
        
        df = pandas.read_sql(query, database_con) 
        cursor.close()
        database_con.close()
        return df

    def get_max_load(self):
        database_con = self.connect()
        cursor = database_con.cursor()

        sql = 'SELECT dbo.GetMaxLoad()'
        rows = cursor.execute(sql)
        for val in rows:
            ret = val

        cursor.close()
        database_con.close()
        return ret[0]

    def get_min_load(self):
        database_con = self.connect()
        cursor = database_con.cursor()

        sql = 'SELECT dbo.GetMinLoad()'
        rows = cursor.execute(sql)
        for val in rows:
            ret = val

        cursor.close()
        database_con.close()
        return ret[0]