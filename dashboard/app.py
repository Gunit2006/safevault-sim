import os
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# Paths to the generated data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
TXN_PATH = os.path.join(DATA_DIR, 'transactions.csv')
LBL_PATH = os.path.join(DATA_DIR, 'labels.csv')

def load_data():
    """Load and join the transactions and labels data."""
    if not os.path.exists(TXN_PATH) or not os.path.exists(LBL_PATH):
        return None
    
    txn_df = pd.read_csv(TXN_PATH)
    lbl_df = pd.read_csv(LBL_PATH)
    
    # Merge for display purposes in the dashboard
    merged_df = pd.merge(txn_df, lbl_df, on='txn_id', how='left')
    # Sort descending by timestamp
    merged_df = merged_df.sort_values('timestamp', ascending=False)
    
    # Fill NaN values for non-merged if any
    merged_df.fillna(False, inplace=True)
    return merged_df

@app.route('/')
def index():
    df = load_data()
    if df is None:
        return render_template('index.html', error="Data not found. Please run the generator first.", summary={}, data=[])
    
    filter_type = request.args.get('filter', 'all')
    
    # Apply filters
    if filter_type == 'scams':
        filtered_df = df[df['is_fraud'] == True]
    elif filter_type == 'normal':
        filtered_df = df[df['is_fraud'] == False]
    else:
        filtered_df = df
        
    # Calculate summary metrics
    summary = {
        'total_txns': len(df),
        'total_scams': len(df[df['is_fraud'] == True]),
        'total_amount': f"₹{df['amount'].sum():,.2f}",
        'scam_amount': f"₹{df[df['is_fraud'] == True]['amount'].sum():,.2f}"
    }
    
    # Convert filtered DataFrame to dictionary for the template, limit to top 500 for performance
    data = filtered_df.head(500).to_dict('records')
    
    return render_template('index.html', summary=summary, data=data, current_filter=filter_type)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')
