from flask import Blueprint, jsonify, request
from models import Medicine, db
from auth import require_api_key
import time

test_dispenser = Blueprint('test_dispenser', __name__)

@test_dispenser.route('/test/dispense/<int:compartment>', methods=['POST'])
@require_api_key
def test_dispense(compartment):
    """Test route to dispense medicine from a specific compartment"""
    if not (1 <= compartment <= 6):
        return jsonify({'error': 'Invalid compartment number'}), 400
        
    from rpi_handler import RaspberryPiHandler
    
    handler = RaspberryPiHandler()
    
    try:
        # Get medicine in this compartment
        medicine = Medicine.query.filter_by(compartment_number=compartment).first()
        if not medicine:
            return jsonify({'error': 'No medicine found in this compartment'}), 404
            
        # Check quantity
        if medicine.quantity < medicine.dosage:
            return jsonify({'error': 'Insufficient quantity'}), 400
            
        # Test dispense
        success = handler._set_servo_angle(compartment, handler.SERVO_DISPENSE)
        if not success:
            return jsonify({'error': 'Failed to control servo'}), 500
            
        time.sleep(1.5)  # Wait for medicine to drop
        
        # Close compartment
        handler._set_servo_angle(compartment, handler.SERVO_CLOSED)
        
        # Update quantity
        medicine.quantity -= medicine.dosage
        db.session.commit()
        
        return jsonify({
            'success': True,
            'medicine': medicine.name,
            'remaining': medicine.quantity,
            'dispensed': medicine.dosage
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        handler.cleanup()