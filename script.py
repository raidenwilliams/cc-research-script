import os
import json
import glob
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

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
        "appId": os.getenv("NEXT_PUBLIC_FIREBASE_APP_ID")
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
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Successfully connected to Firebase!")
    except Exception as e:
        print(f"Failed to connect to Firebase: {e}")
        return
    
    # Look for JSON research data files in 'data' directory
    json_files = glob.glob("data/*.json")
    if not json_files:
        print("No JSON files found in the data directory.")
        return
    
    print(f"Found {len(json_files)} JSON files to process.")
    
    # Process each JSON file
    for file_path in json_files:
        try:
            # Read JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)
            
            # Extract collection name from filename (without extension)
            collection_name = os.path.basename(file_path).split('.')[0]
            
            # Save data to Firebase
            save_to_firebase(db, collection_name, data)
            
            print(f"Successfully processed {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

def save_to_firebase(db, collection_name, data):
    """Save data to Firebase Firestore"""
    collection_ref = db.collection(collection_name)
    
    if isinstance(data, list):
        # If data is a list, add each item as a separate document
        for item in data:
            # Use item ID as document ID if available, otherwise let Firestore generate one
            if 'id' in item:
                collection_ref.document(str(item['id'])).set(item)
            else:
                collection_ref.add(item)
        print(f"Added {len(data)} documents to {collection_name} collection")
    elif isinstance(data, dict):
        # If data is a single object, add as one document
        collection_ref.add(data)
        print(f"Added 1 document to {collection_name} collection")
    else:
        print(f"Unsupported data format in {collection_name}")

if __name__ == "__main__":
    main()
