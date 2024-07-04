import os
from flask import current_app

file_path = os.path.join(current_app.root_path, 'website', 'receipts', 'TCFM_TransactionNo._3.pdf')
print(os.path.isfile(file_path))  # Should return True if the file exists