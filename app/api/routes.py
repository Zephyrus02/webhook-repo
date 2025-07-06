from flask import Blueprint, jsonify
from app.extensions import mongo
from datetime import datetime, timedelta

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/events', methods=['GET'])
def get_events():
    try:
        # Check if mongo is properly initialized
        if mongo.db is None:
            return jsonify({'error': 'Database connection not available'}), 500
            
        # Get events from last 24 hours, sorted by timestamp (newest first)
        events = list(mongo.db.github_events.find(
            {},
            {'_id': 1, 'author': 1, 'event': 1, 'from_branch': 1, 'to_branch': 1, 'timestamp': 1}
        ).sort('timestamp', -1).limit(50))
        
        # Convert ObjectId to string for JSON serialization
        for event in events:
            event['_id'] = str(event['_id'])
            
        return jsonify({
            'events': events,
            'count': len(events)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500