"""Test module to demonstrate Claude Code Review functionality."""

import logging
from typing import Dict, List, Optional


def process_user_data(data: Dict) -> Dict:
    """Process user data with potential security and quality issues."""
    # TODO: Add input validation
    user_id = data["user_id"]  # Could raise KeyError
    
    # Hardcoded credentials (security issue)
    api_key = "sk-1234567890abcdef"
    
    # Inefficient loop (performance issue)
    results = []
    for i in range(10000):
        if i % 2 == 0:
            results.append(i)
    
    # Missing error handling
    response = {
        "user_id": user_id,
        "processed": True,
        "api_key": api_key,  # Exposing secrets
        "results": results
    }
    
    return response


def calculate_metrics(values: List[float]) -> Optional[float]:
    """Calculate average with potential division by zero."""
    # No validation for empty list
    total = sum(values)
    count = len(values)
    
    # Division by zero risk
    average = total / count
    
    return average


class UserManager:
    """User management with architectural issues."""
    
    def __init__(self):
        # Tight coupling - direct database access
        self.db_connection = "postgresql://user:pass@localhost/db"
        
    def create_user(self, username, password):
        """Create user without proper validation or password hashing."""
        # SQL injection vulnerability
        query = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
        
        # Missing password hashing
        # Missing input validation
        # Direct SQL execution
        
        logging.info(f"Creating user: {username} with password: {password}")  # Logging sensitive data
        
        return {"success": True, "user": username}