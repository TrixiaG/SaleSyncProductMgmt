from flask_login import current_user, login_required
from flask import Blueprint, render_template, request, jsonify, flash
from .models import User, db, UserUpdateLog
import datetime


usermanagement = Blueprint('usermanagement', __name__)


@usermanagement.route('/usermgmt')
@login_required
def UserPage():

    users = User.query.all() 

    if current_user.access == 'Admin':
        return render_template("usermanagement.html", users=users)

    else: 
       return render_template("restricted.html", boolean=True)
   

@usermanagement.route('/usermgmt/update', methods=['POST'])
@login_required
def updateuser():
    try:
        data = request.get_json()
        user = User.query.filter_by(eid=data['eid']).first()

        if user:
            log_entries = []

            if user.email != data['email']:
                log_entries.append(UserUpdateLog(user.eid, 'email', current_user.eid))
                user.email = data['email']
            if user.first_name != data['first_name']:
                log_entries.append(UserUpdateLog(user.eid, 'first_name', current_user.eid))
                user.first_name = data['first_name']
            if user.last_name != data['last_name']:
                log_entries.append(UserUpdateLog(user.eid, 'last_name', current_user.eid))
                user.last_name = data['last_name']
            if user.bday != data['bday']:
                log_entries.append(UserUpdateLog(user.eid, 'bday', current_user.eid))
                user.bday = data['bday']
            if user.access != data['access']:
                log_entries.append(UserUpdateLog(user.eid, 'access', current_user.eid))
                user.access = data['access']

            db.session.commit()

            for log_entry in log_entries:
                db.session.add(log_entry)
            db.session.commit()

            
            return jsonify({'message': 'User information updated successfully'}), 200
        else:
            return jsonify({'message': 'User not found'}), 404
        
    except Exception as e:
        print(f"Error updating user information: {str(e)}")
        return jsonify({'message': 'Error updating user information'}), 500
    
    
@usermanagement.route('/usermgmt/details', methods=['GET'])
@login_required
def get_user_details():
    try:
        eid = request.args.get('eid')
        user = User.query.filter_by(eid=eid).first()

        if user:
            user_data = {
                'eid': user.eid,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'bday': user.bday,
                'access': user.access
            }
            return jsonify(user_data), 200
        else:
            return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        print(f"Error fetching user details: {str(e)}")
        return jsonify({'message': 'Error fetching user details'}), 500

@usermanagement.route('/usermgmt/deactivate/<eid>', methods=['POST'])
def deactivate_user(eid):
    user = User.query.filter_by(eid=eid).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.access = 'Deactivated'
    db.session.commit()

    return jsonify({'message': 'User deactivated successfully'})

    
@usermanagement.route('/usermgmt/approve', methods=['POST'])
@login_required
def approveuser():
    try:
        data = request.get_json()
        user = User.query.filter_by(eid=data['eid']).first()

        if user:
            user.access = 'Staff'
            db.session.commit()

            return jsonify({'message': 'User access level updated to Staff', 'eid': user.eid, 'access': user.access}), 200
        else:
            return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        print(f"Error updating user access level: {str(e)}")
        return jsonify({'message': 'Error updating user access level'}), 500
