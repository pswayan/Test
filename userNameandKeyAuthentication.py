from flask import Flask, request, jsonify
import os
import csv
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity

app = Flask(__name__)

# Assuming you have a User model with a 'role' attribute
class User:
    def __init__(self, username, role, api_key):
        self.username = username
        self.role = role
        self.role = api_key

# Sample user data (replace this with your actual user data)
users = [
    User('swapanda', 'IT-QE', 'api_key_1'),
    User('acm1508', 'IT-QE', 'api_key_2'),
    # Add more users as needed
    User('narayana', 'OtherRole', 'api_key_3'),  # Example of a user not in IT-QE
]


# Define folder paths
TEST_DATA_FOLDER = 'Test Data'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEST_DATA_FOLDER'] = TEST_DATA_FOLDER

# Ensure required folders exist
for folder in [UPLOAD_FOLDER, TEST_DATA_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    # Check if the file extension is allowed (only .csv files are allowed)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

def check_second_row_first_column(input_file):
    # Check if there is data available in the 2nd row, 1st column of a CSV file
    with open(input_file, 'r', newline='') as input_csv:
        reader = csv.reader(input_csv)
        rows = list(reader)
        if len(rows) > 1 and rows[1] and rows[1][0]:
            return True
        else:
            return False

def get_and_remove_value(file_path):
    # Get the value from the 2nd row, 1st column and remove the entire 2nd row
    with open(file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows) == 1 :
            return 0
    value = rows[1][0]
    del rows[1]
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)
    return value

def count_non_empty_rows(file_path):
    # Count the number of non-empty rows in a CSV file
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        non_empty_rows = sum(1 for row in csv_reader if any(row))
    return non_empty_rows

def delete_uploaded_csv_files(input_folder):
    # Delete all uploaded CSV files in a folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            os.remove(file_path)

def append_csv_to_existing_file(input_file, output_file):
    # Append the content of one CSV file to another
    with open(input_file, 'r', newline='') as input_csv, open(output_file, 'a', newline='') as output_csv:
        reader = csv.reader(input_csv)
        writer = csv.writer(output_csv)
        for row in reader:
            writer.writerow(row)

def remove_duplicates_and_blanks(input_file, output_file):
    # Remove duplicate and blank rows from a CSV file
    seen_values = set()
    cleaned_data = []
    with open(input_file, 'r', newline='') as input_csv:
        reader = csv.reader(input_csv)
        for row in reader:
            if any(row):
                if tuple(row) not in seen_values:
                    seen_values.add(tuple(row))
                    cleaned_data.append(row)
    with open(output_file, 'w', newline='') as output_csv:
        writer = csv.writer(output_csv)
        writer.writerows(cleaned_data)

@app.route('/upload', methods=['POST'])
def upload_file_api():
    api_key = request.headers.get('API-Key')
    current_user = request.headers.get('Username')  # Assuming you send the username in the headers
 
    # if api_key in valid_api_keys:
    user = next((user for user in users if user.username == current_user), None)
    if user and user.role == 'IT-QE' and user.api_key == api_key:

    # Handle file upload
        if 'file' not in request.files:
            return jsonify({'message': 'No file uploaded'}), 400
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'message': 'Bad request. Please upload a CSV file.'}), 400
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(file_path)
        return jsonify({'message': 'File uploaded successfully'})
    else:
        return jsonify({'message': 'Access forbidden. Invalid API key or user not in the IT-QE team'}), 403


@app.route('/merge_csv', methods=['GET'])
def merge_csv_api():
    api_key = request.headers.get('API-Key')
    current_user = request.headers.get('Username')  # Assuming you send the username in the headers
 
    # if api_key in valid_api_keys:
    user = next((user for user in users if user.username == current_user), None)
    if user and user.role == 'IT-QE' and user.api_key == api_key:

    # Merge uploaded CSV files and remove duplicates/blanks
        current_user = get_jwt_identity()
        user = next((user for user in users if user.username == current_user), None)
        if user and user.role == 'IT-QE':
            input_folder = app.config['UPLOAD_FOLDER']
            test_data_folder = os.path.join(app.config['TEST_DATA_FOLDER'])
            output_file = os.path.join(test_data_folder, 'tsn_list.csv')
            if not os.path.exists(test_data_folder):
                os.makedirs(test_data_folder)
            csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
            if not csv_files:
                return jsonify({'message': 'No files available to merge, Please upload a csv file'}), 400
            # output_file = os.path.join(test_data_folder, 'TSN_Test_Data.csv')
            for csv_file in csv_files:
                input_file_path = os.path.join(input_folder, csv_file)
                append_csv_to_existing_file(input_file_path, output_file)
            remove_duplicates_and_blanks(output_file, output_file)
            delete_uploaded_csv_files(input_folder)
            return jsonify({'message': 'CSV files merged successfully, files deleted from uploads folder'})
    else:
        return jsonify({'message': 'Access forbidden. Invalid API key or user not in the IT-QE team'}), 403


@app.route('/get_and_remove_value/<filename>', methods=['GET'])
def get_and_remove_value_api(filename):
    # Get a value from the 2nd row, 1st column and remove the entire 2nd row from a CSV file
    file_path = os.path.join(app.config['TEST_DATA_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'message': 'File not found'}), 404
    if not check_second_row_first_column(file_path):
        return jsonify({'message': 'No TSN available, please upload a TSN file(.csv)'}), 404
    value = get_and_remove_value(file_path)
    data_count = count_non_empty_rows(file_path)
    if data_count <= 6:
        warning_message = "You are running out of TSNs, Please upload a TSN file(.csv)"
    else:
        warning_message = None
    return jsonify({'value': value, 'TSN_Count': data_count, 'warning_message': warning_message})


@app.route('/fetchTsn', methods=['GET'])
def get_tsn():
    api_key = request.headers.get('API-Key')
    current_user = request.headers.get('Username')  # Assuming you send the username in the headers
 
    # if api_key in valid_api_keys:
    user = next((user for user in users if user.username == current_user), None)
    if user and user.role == 'IT-QE' and user.api_key == api_key:
    
        # Get a value from the 2nd row, 1st column and remove the entire 2nd row from a CSV file
        current_user = get_jwt_identity()
        user = next((user for user in users if user.username == current_user), None)
        if user and user.role == 'IT-QE':
            default_path = os.path.join('Test Data','tsn_list.csv')
            data_count = count_non_empty_rows(default_path) -1
            if data_count == 0 :
                return jsonify({'message' : 'TSN Bucket is empty'})
            value = get_and_remove_value(default_path)
            if data_count <= 6:
                warning_message = "You are running out of TSNs, Please upload a TSN file(.csv)"
            else:
                warning_message = None
            return jsonify({'value': value, 'TSN_Count': data_count, 'warning_message': warning_message})
    else:
        return jsonify({'message': 'Access forbidden. You are not in the IT-QE team'}), 403


if __name__ == '__main__':
    app.run(debug=True)