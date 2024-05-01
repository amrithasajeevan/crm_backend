from google.oauth2 import service_account
from googleapiclient.discovery import build
# Set up credentials
SCOPES = ['https://www.googleapis.com/auth/forms.responses.readonly']
SERVICE_ACCOUNT_FILE =''
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# Build the service
service = build('forms', 'v1', credentials=creds)
# Google Form ID
form_id = ''
# Fetch responses
response = service.forms().responses().list(formId=form_id).execute()
# Process responses
if 'responses' in response:
    for item in response['responses']:
        # Process each response item as needed
        print(item)
else:
    print('No responses found.') 