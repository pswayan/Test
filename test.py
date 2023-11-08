from flask import Flask, request, jsonify
import os
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Assuming you have a User model with a 'role' attribute
class User:
    def __init__(self, username, role):
        self.username = username
        self.role = role
        
# Sample user data (replace this with your actual user data)
secret_key = 'ec9cd08045574016ac9cdb2e1d7d9c667b2f76c5bd085321b34be13047acf01c'
users = [
    User('swapanda', 'IT-QE'),
    User('acm', 'IT-QE'),
    User('ghegde', 'IT-QE'),
    # Add more users as needed
    User('otheruser', 'OtherRole'),  # Example of a user not in IT-QE
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
    api_key = request.headers.get('API-Key') # Sending the API-Key in the headers
    current_user = request.headers.get('Username')  # Sending the username in the headers
       
    print(f'API Key: {api_key}')
    print(f'Current User: {current_user}')
    
    # Validation of Username and Role:
    user = next((user for user in users if user.username == current_user), None)
    if user and user.role == 'IT-QE'and api_key == secret_key:
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
    api_key = request.headers.get('API-Key') # Sending the API-Key in the headers
    current_user = request.headers.get('Username')  # Sending the username in the headers
 
    # Validation of Username and Role:
    user = next((user for user in users if user.username == current_user), None)
    if user and user.role == 'IT-QE'and api_key == secret_key:

    # Merge uploaded CSV files and remove duplicates/blanks
        input_folder = app.config['UPLOAD_FOLDER']
        test_data_folder = os.path.join(app.config['TEST_DATA_FOLDER'])
        output_file = os.path.join(test_data_folder, 'tsn_list.csv')
        if not os.path.exists(test_data_folder):
            os.makedirs(test_data_folder)
        csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
        if not csv_files:
            return jsonify({'message': 'No files available to merge, Please upload a csv file'}), 400
        for csv_file in csv_files:
            input_file_path = os.path.join(input_folder, csv_file)
            append_csv_to_existing_file(input_file_path, output_file)
        remove_duplicates_and_blanks(output_file, output_file)
        delete_uploaded_csv_files(input_folder)
        return jsonify({'message': 'CSV files merged successfully, files deleted from uploads folder'})
    else:
        return jsonify({'message': 'Access forbidden. Invalid API key or user not in the IT-QE team'}), 403

@app.route('/fetchTsn', methods=['GET'])
def get_tsn():
    api_key = request.headers.get('API-Key') # Sending the API-Key in the headers
    current_user = request.headers.get('Username')  # Sending the username in the headers
 
    # Validation of Username and Role:
    user = next((user for user in users if user.username == current_user), None)
    if user and user.role == 'IT-QE'and api_key == secret_key:
    
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
        return jsonify({'message': 'Access forbidden. Invalid API key or user not in the IT-QE team'}), 403

if __name__ == '__main__':
    app.run(debug=True)