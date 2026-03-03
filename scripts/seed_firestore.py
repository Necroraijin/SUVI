import firebase_admin
from firebase_admin import credentials, firestore

def seed_database():
    print("🌱 Seeding Firestore with initial SUVI OS memory...")
    
    # This automatically uses the credentials you generated in setup_gcp.bat
    firebase_admin.initialize_app()
    db = firestore.client()

    # Create the core user profile document
    profile_ref = db.collection('user_profile').document('main')
    profile_ref.set({
        'name': 'Creator',
        'age': 22,
        'profession': 'Electronics and CS Engineer',
        'partner': 'Sunidhi',
        'active_projects': ['SUVI OS', 'Azzurite Browser', 'Defense Manufacturing Startup']
    })

    # Add initial permissions
    permissions_ref = db.collection('system_config').document('permissions')
    permissions_ref.set({
        'allow_file_system_write': True,
        'allow_browser_automation': True,
        'strict_mode': True
    })

    print("✅ Database seeded successfully. SUVI's memory is online.")

if __name__ == "__main__":
    seed_database()