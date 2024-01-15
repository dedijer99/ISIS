from datetime import datetime, timedelta
import os
from flask import jsonify
from data.database import DataBase
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np
from joblib import dump, load   

NUMBER_OF_COLUMNS = 16
SHARE_FOR_TRAINING = 0.85

class ModelCreator:
    def __init__(self):
        self.database = DataBase()
        self.modelPath = ''
        self.predicted_data = []
        self.predicted_date = None

    def start_model_training(self, yearFrom, monthFrom, dayFrom, yearTo, monthTo, dayTo):
        self.dataframe = self.load_data(yearFrom, monthFrom, dayFrom, yearTo, monthTo, dayTo)
        self.dataframe.fillna(method="ffill", inplace=True)
        
        print(self.dataframe.columns)
        for col in self.dataframe.columns:
            print(col)
        X = self.dataframe.drop(['Load'], axis=1)
        y = self.dataframe['Load']

        # first solution

        # Splitting the data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        # Model training
        model = RandomForestRegressor()
        model.fit(X_train, y_train)
        
        # Model evaluation
        predictions = model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        print("Root Mean Squared Error: ", rmse)

        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define the filename with the timestamp
        filename = f"{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f'models/model_{current_timestamp}.joblib')}"
        dump(model, filename)

        print(f"Model saved as: {filename}")

    def predict(self, days, yearFrom, monthFrom, dayFrom, model_name):
        self.predicted_date = datetime(yearFrom, monthFrom, dayFrom)

        date_to = datetime(yearFrom, monthFrom, dayFrom) + timedelta(days=days - 1)
        self.dataframe = self.load_test_data(yearFrom, monthFrom, dayFrom, date_to.year, date_to.month, date_to.day) 
                                                                          #SHARE_FOR_TRAINING           
        
        X = self.dataframe.drop(['Load'], axis=1, errors='ignore')
        model = load(f"{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f'models/{model_name}')}")
        self.dataframe['Load'] = model.predict(X)
        
        columns_to_export = ['Hour', 'Day', 'Month', 'Year', 'Load']
        
        self.dataframe.to_csv("csv_filename.csv", index=False, columns=columns_to_export)
        
        self.dataframe['Timestamp'] = pd.to_datetime(self.dataframe[['Year', 'Month', 'Day', 'Hour']])
        
        dates = self.dataframe['Timestamp'].tolist()
        data = self.dataframe['Load'].tolist()
        
        return jsonify({"data": data, "dates": dates})

    def get_csv(self):
        if self.predicted_data == []:
            return {"error": "Error! No prediction!"}, 400
        
        rescaled_data, dates = self.scale_back()
        self.generate_csv(rescaled_data, dates)
        return {"data": "OK"}, 200

    def set_path(self, path):
        self.path = path

    def get_path(self):
        return os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models'), self.path)

    def load_data(self, yearFrom, monthFrom, dayFrom, yearTo, monthTo, dayTo):
        print("Load data started", datetime.now())
        dataframe = self.database.get_pandas_dataframe(yearFrom, monthFrom, dayFrom, yearTo, monthTo, dayTo, True)
        print("Load data finished", datetime.now())
        return dataframe

    def load_test_data(self, yearFrom, monthFrom, dayFrom, yearTo, monthTo, dayTo):
        print("Load data started", datetime.now())
        dataframe = self.database.get_pandas_dataframe(yearFrom, monthFrom, dayFrom, yearTo, monthTo, dayTo, False)
        print("Load data finished", datetime.now())
        return dataframe