# CourseConnect Research Data Import Tool

This repository contains a Python script for processing and uploading research project listings to the [CourseConnect Research](https://github.com/courseconnect-team/courseconnect) page using Firebase Firestore. The tool parses JSON data containing research project information, formats it correctly, and optionally uploads it to the Firebase database.

The JSON data used in the project is created from the [uf-research-labs-data](https://github.com/raidenwilliams/uf-research-labs-data) repository. If more data is needed in the future please navigate there.

## Overview

The tool performs the following functions:
- Reads research project data from JSON files in the `data` directory
- Processes faculty mentor and PhD student mentor information into the required format
- Creates a standardized data structure for each research listing
- Saves the processed data to a timestamped JSON file in the `output` directory
- Optionally uploads the processed data to Firebase Firestore

## Prerequisites

- Python 3.6+
- Firebase project with Firestore database
- Firebase service account credentials

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/cc-research-script.git
   cd cc-research-script
   ```

2. Create and activate a virtual environment:
   ```
   # Using venv
   python -m venv env
   
   # On Windows
   env\Scripts\activate
   
   # On macOS/Linux
   source env/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

### Firebase Setup

1. Create a Firebase project at [https://console.firebase.google.com/](https://console.firebase.google.com/)

2. Set up Firestore database in your Firebase project

3. Generate a private key for your service account:
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file as `serviceAccount.json` in the root directory of this project

4. Create a `.env` file in the project root with the following Firebase configuration:
   ```
   NEXT_PUBLIC_FIREBASE_API_KEY="your_api_key"
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="your_project_id.firebaseapp.com"
   NEXT_PUBLIC_FIREBASE_PROJECT_ID="your_project_id"
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET="your_project_id.appspot.com"
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID="your_messaging_sender_id"
   NEXT_PUBLIC_FIREBASE_APP_ID="your_app_id"
   FIREBASE_COLLECTION_NAME="data_destination_collection_name"
   ```

### Data Preparation

Place your JSON files containing research project data in the `data` directory. The expected format should match the structure in the provided `data/all_projects.json` file.

## Usage

1. Run the script:
   ```
   python script.py
   ```

2. The script will:
   - Process all JSON files in the `data` directory
   - Save the processed data to the `output` directory with a timestamp
   - Ask if you want to upload the data to Firebase

3. If you choose to upload to Firebase, the script will:
   - Connect to Firebase using your service account credentials
   - Upload each research listing to the "research-listings" collection
   - Create an empty "applications" subcollection for each listing

## Data Structure

The script expects input JSON files to have the following structure:

```json
[
  {
    "project_title": "Example Research Project",
    "department": "Computer and Information Sciences and Engineering",
    "faculty_mentor": "Faculty Name, faculty@ufl.edu",
    "terms_available": "Fall, Spring, Summer",
    "student_level": "Junior, Senior",
    "prerequisites": "Programming experience, coursework in related field",
    "credit": "0-3 credits via EGN 4912",
    "stipend": "None unless selected for University Scholars",
    "application_requirements": "Resume, transcript, faculty interview",
    "application_deadline": "Rolling basis",
    "website": "https://example.com",
    "project_description": "Description of the research project",
    "ph.d._student_mentor(s)": "PhD Student, phd@ufl.edu"
  }
]
```

### Data Processing and Transformation

The script transforms the input JSON data for Firebase Firestore storage:

1. **What's Being Parsed**:
   - `faculty_mentor`: Parses name and email from strings like "Faculty Name, faculty@ufl.edu"
   - `ph.d._student_mentor(s)`: Similarly extracts name and email information

2. **How Data is Restructured**:
   From this raw input format:
   ```json
   {
     "project_title": "Example Research Project",
     "faculty_mentor": "Faculty Name, faculty@ufl.edu",
     "ph.d._student_mentor(s)": "PhD Student, phd@ufl.edu"
     // ... other fields
   }
   ```

   To a Firestore-ready format:
   ```json
   {
     "data": {
       "project_title": "Example Research Project",
       "department": "Computer and Information Sciences and Engineering",
       "faculty_mentor": {
            "lanthony@cise.ufl.edu": "Lisa Anthony"
        },
        "phd_student_mentor": {
            "info": "TBD based on project and availability"
        },
       // ... other fields preserved
     }
   }
   ```

3. **Benefits of This Structure**:
   - Makes querying more efficient in Firestore
   - Separates data components for better display and filtering
   - Includes required metadata for the CourseConnect Research platform
   - Enables proper functioning of the application system for each research listing

## Important Notes

- **Service Account Keys**: Never commit your `serviceAccount.json` file to version control. It contains sensitive credentials.
- **Firebase Security**: Ensure your Firestore database has appropriate security rules to protect the data.

## Output

The processed data will be saved to the `output` directory with a filename like `all_processed_data_YYYYMMDD_HHMMSS.json`. This file contains the transformed data ready for upload to Firebase.

When uploaded to Firebase, each research listing will be added to the collection that you specify in the .env in the FIREBASE_COLLECTION_NAME section. For CourseConnect we use the "research-listings" collection with an auto-generated document ID, and an empty "applications" subcollection will be created for each listing.