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

class ModelFactory:
    def __init__(self):
        self.database = DataBase()
        self.modelPath = ''
        self.predicted_data = []
        self.predicted_date = None

    def initiate_training_procedure(self, startYear, startMonth, startDay, endYear, endMonth, endDay):
        def prepare_data(year_start, month_start, day_start, year_end, month_end, day_end):
            df = self.load_data(year_start, month_start, day_start, year_end, month_end, day_end)
            df.fillna(method="ffill", inplace=True)
            return df

        def save_model(rf_model, timestamp):
            file_path = f"models/model_{timestamp}.joblib"
            full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
            dump(rf_model, full_path)
            return full_path

        dataset = prepare_data(startYear, startMonth, startDay, endYear, endMonth, endDay)
        
        [print(column_name) for column_name in dataset.columns]

        features = dataset.drop(['Load'], axis=1)
        target = dataset['Load']

        features_train, features_test, target_train, target_test = train_test_split(features, target, test_size=0.2, shuffle=False)

        forest_model = RandomForestRegressor()
        forest_model.fit(features_train, target_train)

        target_predictions = forest_model.predict(features_test)
        error_rmse = np.sqrt(mean_squared_error(target_test, target_predictions))
        print(f"Root Mean Squared Error: {error_rmse}")

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_file = save_model(forest_model, current_time)
        print(f"Model stored at: {model_file}")

    def execute_forecast(self, forecast_days, start_year, start_month, start_day, trained_model_name):
        def load_model(model_file_name):
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f'models/{model_file_name}')
            return load(path)

        def prepare_and_save_results(df, file_name, columns):
            df['CombinedTimestamp'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour']])
            timestamps = df['CombinedTimestamp'].tolist()
            forecasted_load = df['PredictedLoad'].tolist()
            df.to_csv(file_name, index=False, columns=columns)
            return timestamps, forecasted_load

        forecast_start_date = datetime(start_year, start_month, start_day)
        forecast_end_date = forecast_start_date + timedelta(days=forecast_days - 1)
        forecast_data = self.load_test_data(start_year, start_month, start_day, forecast_end_date.year, forecast_end_date.month, forecast_end_date.day)

        feature_data = forecast_data.drop(['Load'], axis=1, errors='ignore')
        prediction_model = load_model(trained_model_name)
        forecast_data['PredictedLoad'] = prediction_model.predict(feature_data)

        export_columns = ['Hour', 'Day', 'Month', 'Year', 'PredictedLoad']
        final_file_name = "predicted_loads.csv"

        timestamps, forecasted_loads = prepare_and_save_results(forecast_data, final_file_name, export_columns)
        
        return jsonify({"data": forecasted_loads, "dates": timestamps})

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