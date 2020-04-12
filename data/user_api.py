from flask import Blueprint, jsonify, request
from data import db_session
from data.users import User

blueprint = Blueprint('user_api', __name__,
                      template_folder='templates')


@blueprint.route('/api/user/<int:user_id>', methods=['GET'])
def get_one_user(user_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'name': user.to_dict(only='name')
        }
    )
