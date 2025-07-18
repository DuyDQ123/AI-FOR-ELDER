from app import app
from models import db, Medicine
import sqlalchemy as sa

def fix_database():
    with app.app_context():
        try:
            # Drop existing constraint if it exists
            db.engine.execute("ALTER TABLE medicines DROP INDEX medicines_unique_compartment")
            print("Dropped existing constraint")
        except Exception as e:
            print(f"No existing constraint to drop: {e}")
        
        try:
            # Add correct constraint
            db.engine.execute("ALTER TABLE medicines ADD CONSTRAINT medicines_unique_compartment UNIQUE (user_id, compartment_number)")
            print("Added correct constraint")
        except Exception as e:
            print(f"Error adding constraint: {e}")
        
        # Check current medicines
        medicines = Medicine.query.all()
        print('\nCurrent medicines in database:')
        for med in medicines:
            print(f'ID: {med.id}, Name: {med.name}, User: {med.user_id}, Compartment: {med.compartment_number}')
        
        # Check if user 3 has compartment 2
        user3_comp2 = Medicine.query.filter_by(user_id=3, compartment_number=2).first()
        if user3_comp2:
            print(f'\nUser 3 has compartment 2: {user3_comp2.name}')
        else:
            print('\nUser 3 does NOT have compartment 2')

if __name__ == '__main__':
    fix_database()