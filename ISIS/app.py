import os
from flask import Flask, request
from werkzeug.utils import secure_filename
from flask_cors import CORS
from services.model_factory import ModelFactory
from services.preprocessor import Preprocessor

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'test_files')
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
CORS(app)

app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
data_preprocessor = Preprocessor(UPLOAD_FOLDER)
model_factory = ModelFactory()

@app.route("/")
def main():
    models = data_preprocessor.get_all_models()
    return {"data": models}, 200

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/model/train', methods=['POST'])
def train_model():
    try:
        start_date = parse_date(request.form['dateFrom'])
        end_date = parse_date(request.form['dateTo'])
    except KeyError as e:
        return {"error": f"Missing parameter: {e}"}, 400
    except ValueError as e:
        return {"error": f"Invalid parameter value: {e}"}, 400

    initiate_training(start_date, end_date)
    return {"data": "OK"}, 200

@app.route('/api/forecast-data', methods=['POST'])
def handle_forecast_data_upload():
    try:
        files_count = get_files_count(request.form)
        process_uploaded_files(request, files_count)
    except ValueError as e:
        return {"error": str(e)}, 400

    data_preprocessor.process_data()
    return {"data": "OK"}, 200

@app.route('/api/forecast-data/predict', methods=['POST'])
def predict_forecast():
    try:
        model_path = request.form['model']
        forecast_days = int(request.form['days'])
        forecast_date = parse_date(request.form['date'])
    except KeyError as e:
        return {"error": f"Missing parameter: {e}"}, 400
    except ValueError as e:
        return {"error": f"Invalid parameter value: {e}"}, 400

    return model_factory.execute_forecast(forecast_days, *forecast_date, model_path)

def parse_date(date_str: str) -> tuple:
    try:
        year, month, day = map(int, date_str.split('-'))
        return year, month, day
    except ValueError:
        raise ValueError("Date must be in 'YYYY-MM-DD' format")
    
def get_files_count(form_data):
    if 'filesLength' not in form_data:
        raise ValueError("No file part in the request")

    files_length = int(form_data['filesLength'])
    if files_length <= 0:
        raise ValueError("No selected files")
    
    return files_length

def initiate_training(start_date: tuple, end_date: tuple):
    if start_date == end_date:
        model_factory.initiate_training_procedure(0, 0, 0, 0, 0, 0)
    else:
        model_factory.initiate_training_procedure(*start_date, *end_date)

def process_uploaded_files(request, files_count):
    for i in range(files_count):
        file = request.files[f'file[{i}]']
        validate_and_save_file(file)

def validate_and_save_file(file):
    if file.filename == '':
        raise ValueError("Empty file uploaded")
    if not allowed_file(file.filename):
        raise ValueError("Unsupported file format")

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
def parse_date(date_str: str) -> tuple:
    try:
        year, month, day = map(int, date_str.split('-'))
        return year, month, day
    except ValueError:
        raise ValueError("Date must be in 'YYYY-MM-DD' format")
    
if __name__ == "__main__":
    app.run(debug = True)