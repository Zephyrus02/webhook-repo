from flask import Blueprint, json, request
from datetime import datetime
from typing import Dict, Any
from app.extensions import mongo
from flask import current_app

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

@webhook.route('/receiver', methods=["POST"])
def receiver():
    current_app.logger.info(f"Received webhook request")
    current_app.logger.info(f"Headers: {dict(request.headers)}")
    
    try:
        # Get GitHub event headers
        event_type = request.headers.get('X-GitHub-Event')
        delivery_id = request.headers.get('X-GitHub-Delivery')
        
        current_app.logger.info(f"Event type: {event_type}, Delivery ID: {delivery_id}")
        
        if not event_type:
            return {"error": "Missing X-GitHub-Event header"}, 400
        
        # Parse JSON payload
        payload = request.get_json()
        if not payload:
            return {"error": "Invalid JSON payload"}, 400
            
        # Extract common data
        event_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Handle different event types
        if event_type == "push":
            event_data.update({
                "author": payload.get("pusher", {}).get("name", "Unknown"),
                "event": "push",
                "from_branch": None,  # Push doesn't have from_branch
                "to_branch": payload.get("ref", "").replace("refs/heads/", "") if payload.get("ref") else None
            })
        
        elif event_type == "pull_request":
            action = payload.get("action")
            pr = payload.get("pull_request", {})
            
            # Check if it's a merge event
            if action == "closed" and pr.get("merged"):
                event_data.update({
                    "author": pr.get("merged_by", {}).get("login", "Unknown"),
                    "event": "merge",
                    "from_branch": pr.get("head", {}).get("ref"),
                    "to_branch": pr.get("base", {}).get("ref")
                })
            else:
                # Regular pull request event
                event_data.update({
                    "author": pr.get("user", {}).get("login", "Unknown"),
                    "event": "pull_request",
                    "from_branch": pr.get("head", {}).get("ref"),
                    "to_branch": pr.get("base", {}).get("ref")
                })
        
        else:
            # Skip unsupported events
            return {"message": f"Event type '{event_type}' not processed"}, 200
            
        # Insert into MongoDB
        if mongo.db is None:
            current_app.logger.error("MongoDB connection not initialized")
            return {"error": "Database connection not available"}, 500
        
        result = mongo.db.github_events.insert_one(event_data)
        
        current_app.logger.info(f"Inserted event: {event_data}")
        
        return {
            "message": "Event processed successfully",
            "event_id": str(result.inserted_id),
            "event_type": event_type,
            "event": event_data.get("event")
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Webhook processing error: {str(e)}")
        return {"error": f"Failed to process webhook: {str(e)}"}, 500

# Add a simple test route
@webhook.route('/test', methods=["GET"])
def test():
    return {"message": "Webhook endpoint is working"}, 200
