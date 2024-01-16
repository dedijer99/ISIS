from datetime import datetime, timedelta
import os
from flask import jsonify
from data.database import DataBase
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from keras.models import Sequential, load_model
from keras.layers import Dense
import numpy as np

class ModelFactory:
    def __init__(self):
        self.database = DataBase()
        self.modelPath = ''

    def initiate_training_procedure(self, startYear, startMonth, startDay, endYear, endMonth, endDay):
        def prepare_data(year_start, month_start, day_start, year_end, month_end, day_end):
            df = self.load_data(year_start, month_start, day_start, year_end, month_end, day_end)
            df.fillna(method="ffill", inplace=True)
            return df

        def save_model(model, timestamp):
            file_path = f"models/model_{timestamp}.h5"
            full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
            model.save(full_path)
            return full_path

        dataset = prepare_data(startYear, startMonth, startDay, endYear, endMonth, endDay)
        
        [print(column_name) for column_name in dataset.columns]

        features = dataset.drop(['Load'], axis=1).astype(float)
        target = dataset['Load'].astype(float)

        features_train, features_test, target_train, target_test = train_test_split(features, target, test_size=0.2, shuffle=False)

        model = Sequential()
        model.add(Dense(256, activation='relu', input_shape=(features_train.shape[1],)))
        model.add(Dense(128, activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(1, activation='linear'))

        model.compile(optimizer='adam', loss='mean_squared_error')

        model.fit(features_train, target_train, epochs=100, batch_size=32)

        target_predictions = model.predict(features_test)
        error_rmse = np.sqrt(mean_squared_error(target_test, target_predictions))
        print(f"Root Mean Squared Error: {error_rmse}")

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_file = save_model(model, current_time)
        print(f"Model stored at: {model_file}")

    def execute_forecast(self, forecast_days, start_year, start_month, start_day, trained_model_name):
        def load_model_file(model_file_name):
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f'models/{model_file_name}')
            return load_model(path)

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
        prediction_model = load_model_file(trained_model_name)
        forecast_data['PredictedLoad'] = prediction_model.predict(feature_data.astype(float))

        export_columns = ['Hour', 'Day', 'Month', 'Year', 'PredictedLoad']
        final_file_name = "predicted_loads.csv"

        timestamps, forecasted_loads = prepare_and_save_results(forecast_data, final_file_name, export_columns)
        
        return jsonify({"data": forecasted_loads, "dates": timestamps})

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