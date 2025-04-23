import os
import json
import glob
import re
from time import sleep
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

def main():
    # Load environment variables from .env
    load_dotenv()
    
    # Extract Firebase configuration from environment variables
    firebase_config = {
        "apiKey": os.getenv("NEXT_PUBLIC_FIREBASE_API_KEY"),
        "authDomain": os.getenv("NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("NEXT_PUBLIC_FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("NEXT_PUBLIC_FIREBASE_APP_ID"),
        "collection_name": os.getenv("FIREBASE_COLLECTION_NAME"),
    }
    
    # Check if all necessary Firebase config values are present
    missing_configs = [key for key, value in firebase_config.items() if not value]
    if missing_configs:
        print(f"Error: Missing Firebase configurations: {', '.join(missing_configs)}")
        return
    
    print(f"Using Firebase project: {firebase_config['projectId']}")
    
    # Initialize Firebase (Using default service account credentials or generate a private key from Firebase console)
    try:
        # You'll need to generate a service account key from Firebase console and place it in the project directory
        cred = credentials.Certificate("serviceAccount.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Successfully connected to Firebase!")
    except Exception as e:
        print(f"Failed to connect to Firebase: {e}")
        return
    
    # Find all JSON files in the data directory
    json_files = glob.glob("data/*.json")
    if not json_files:
        print("No JSON files found in the data directory")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    # Process all JSON files
    all_processed_data = []
    
    for json_file_path in json_files:
        try:
            # Read JSON file
            with open(json_file_path, 'r') as file:
                research_projects = json.load(file)
            
            file_name = os.path.basename(json_file_path)
            print(f"Processing {file_name}: Loaded {len(research_projects)} research projects")
            
            # Process data from this file
            file_processed_data = process_research_projects(research_projects)
            
            # Add to our collection of all processed data
            all_processed_data.extend(file_processed_data)
            
            print(f"Successfully processed {len(file_processed_data)} entries from {file_name}")
            
        except Exception as e:
            print(f"Error processing {json_file_path}: {e}")
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Generate timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"output/all_processed_data_{timestamp}.json"
    
    # Write all processed data to JSON file
    with open(output_filename, 'w') as outfile:
        json.dump(all_processed_data, outfile, indent=2)
    
    print(f"All processed data saved to {output_filename}")
    print(f"Total entries: {len(all_processed_data)}")
    
    # Ask user if they want to proceed with Firebase upload
    upload_to_firebase = input("Would you like to upload this data to Firebase? (y/n): ").lower().strip()
    
    if upload_to_firebase == 'y':
        # Save data to Firebase
        save_research_projects_to_firebase(db, all_processed_data, firebase_config)
        print(f"Successfully uploaded all data to Firebase")
    else:
        print("Firebase upload skipped")

def process_research_projects(research_projects):
    """Process research projects into the format needed for Firebase"""
    processed_data = []
    
    for idx, project in enumerate(research_projects):
        try:
            # Parse faculty mentor into the required format
            faculty_mentor_raw = project.get("faculty_mentor", "")
            faculty_mentor = parse_faculty_mentor(faculty_mentor_raw)
            
            # Parse PhD student mentor into the required format
            phd_mentor_raw = project.get("ph.d._student_mentor(s)", "")
            phd_mentor = parse_phd_mentor(phd_mentor_raw)
            
            # Map to the expected field names in the Firebase collection
            firebase_project = {
                "project_title": project.get("project_title", ""),
                "project_description": project.get("project_description", ""),
                "department": project.get("department", ""),
                "faculty_mentor": faculty_mentor, # Parsed map
                "phd_student_mentor": phd_mentor, # Parsed map or string
                "prerequisites": project.get("prerequisites", ""),
                "application_requirements": project.get("application_requirements", ""),
                "application_deadline": project.get("application_deadline", ""),
                "stipend": project.get("stipend", ""),
                "credit": project.get("credit", ""),
                "terms_available": project.get("terms_available", ""),
                "student_level": project.get("student_level", ""),
                "website": project.get("website", ""),
            }
            
            # Just add the firebase_project directly without specifying an ID
            processed_data.append(firebase_project)
            
        except Exception as e:
            print(f"Error processing project: {e}")
    
    return processed_data

def parse_faculty_mentor(mentor_string):
    """
    Parse faculty mentor string to a map with email:name pairs
    Example input: "Lisa Anthony, lanthony@cise.ufl.edu"
    Example output: {"lanthony@cise.ufl.edu": "Lisa Anthony"}
    """
    if not mentor_string:
        return {}
    
    result = {}
    # Simple regex to extract email addresses from the string
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', mentor_string)
    
    for email in emails:
        # Find the name associated with this email
        # Look for text before the email that doesn't contain another email
        name_match = re.search(r'([^@,]+),?\s*' + re.escape(email), mentor_string)
        if name_match:
            name = name_match.group(1).strip()
        else:
            # If we can't match directly, take everything before the email and hope it's right
            parts = mentor_string.split(email)
            name = parts[0].strip().rstrip(',')
        
        # Add email and name to the map
        result[email] = name
    
    return result

def parse_phd_mentor(mentor_string):
    """
    Parse PhD student mentor string to a map with email:name pairs
    Example input: "Xiaofeng Zhou, xiaofengzhou@ufl.edu; Miguel Rodriguez, miguelrodriguez@ufl.edu"
    Example output: {"xiaofengzhou@ufl.edu": "Xiaofeng Zhou", "miguelrodriguez@ufl.edu": "Miguel Rodriguez"}
    If no emails found, return the original string as a special field
    """
    if not mentor_string:
        return {}
    
    # Check if there are emails in the string
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', mentor_string)
    
    # If no emails found, return the original string in a special format
    if not emails:
        return {"info": mentor_string}
    
    result = {}
    # Split by semicolons to handle multiple mentors
    mentor_parts = mentor_string.split(";")
    
    for part in mentor_parts:
        part = part.strip()
        # Find emails in this part
        part_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', part)
        
        if part_emails:
            for email in part_emails:
                # Find the name associated with this email
                name_match = re.search(r'([^@,]+),?\s*' + re.escape(email), part)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    # If we can't match directly, take everything before the email
                    parts = part.split(email)
                    name = parts[0].strip().rstrip(',')
                
                # Add email and name to the map
                result[email] = name
        else:
            # If no emails found in this part, add the entire part with a generic key
            if part:
                result[f"info_{len(result)}"] = part
    
    return result

def save_research_projects_to_firebase(db, processed_data, firebase_config):
    """Save processed data to Firebase Firestore"""
    collection_ref = db.collection(firebase_config["collection_name"])
    
    if not isinstance(processed_data, list):
        print("Error: Expected processed data to be a list")
        return
    
    added_count = 0
    
    # Process each research project
    for project_data in processed_data:
        try:
            # Let Firebase generate the document ID
            doc_ref = collection_ref.document()
            doc_ref.set(project_data)
            
            # Get the auto-generated ID
            doc_id = doc_ref.id
            
            # Create applications subcollection reference (no documents needed)
            applications_collection = doc_ref.collection("applications")
            
            added_count += 1
            print(f"Added project with auto-generated ID: {doc_id}")
            
            sleep(0.5)  # Optional: Add a small delay to avoid hitting Firestore limits
            
        except Exception as e:
            print(f"Error adding project to Firebase: {e}")
    
    print(f"Added {added_count} research projects to research-listings collection")

if __name__ == "__main__":
    main()
