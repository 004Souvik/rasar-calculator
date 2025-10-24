from flask import Flask, request, jsonify, send_file
import pandas as pd
import io
import os
from rasar_desc import rasar_desc_calculation
from flask_cors import CORS
app = Flask(__name__)
CORS(app)



@app.route('/calculate_rasar', methods=['POST'])
def calculate_rasar():
    try:
        # Get the uploaded files and method
        train_file = request.files.get('train_file')
        test_file = request.files.get('test_file')
        method = request.form.get('method', 'Gaussian Kernel')
        descriptor_type = request.form.get('descriptor_type', 'User Defined Descriptors')

        if not train_file or not test_file:
            return jsonify({'error': 'Both training and test files are required'}), 400

        # Read Excel files into pandas DataFrames
        df_train = pd.read_excel(train_file, index_col=0)
        df_test = pd.read_excel(test_file, index_col=0)

        # Validate DataFrames
        if df_train.empty or df_test.empty:
            return jsonify({'error': 'Uploaded files are empty or invalid'}), 400

        # Call the RASAR descriptor calculation function
        result = rasar_desc_calculation(df5=df_train, df6=df_test, des=descriptor_type, method=method)
        result1 = rasar_desc_calculation(df5=df_train, df6=df_train, des=descriptor_type, method=method)

        # Convert results to DataFrame
        result_df = pd.DataFrame(result, index=df_test.index)
        result_df1 = pd.DataFrame(result1, index=df_train.index)

        # Save results to an in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output) as writer:
            result_df1.to_excel(writer, sheet_name='Train')
            result_df.to_excel(writer, sheet_name='Test')
        output.seek(0)

        # Return the Excel file as a downloadable response
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='rasar_descriptors_output.xlsx'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port)