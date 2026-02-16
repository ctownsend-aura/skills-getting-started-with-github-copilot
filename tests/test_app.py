"""
Tests for the Mergington High School Activities API

Tests cover all API endpoints and error cases to ensure the application
functions correctly.
"""

import pytest
import sys
import os
from pathlib import Path

# Add src directory to Python path so we can import app
sys.path.insert(0, os.path.join(Path(__file__).parent, '..', 'src'))

from fastapi.testclient import TestClient
from app import app, activities

# Create test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to their initial state before each test"""
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for interscholastic play",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["marcus@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Develop tennis skills and participate in matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["alex@mergington.edu", "taylor@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and mixed media techniques",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["isabella@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in school plays and theatrical productions",
            "schedule": "Thursdays, 3:30 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu", "sophie@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop argumentation and public speaking skills",
            "schedule": "Mondays and Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 12,
            "participants": ["ryan@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Compete in science competitions and experiments",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["aisha@mergington.edu", "james@mergington.edu"]
        }
    }
    
    # Clear current activities and restore originals
    activities.clear()
    activities.update(original_activities)
    
    yield  # Run the test
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestRoot:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self, reset_activities):
        """Test that we can retrieve all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activity_structure(self, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_activity_participants(self, reset_activities):
        """Test that activities contain correct initial participants"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert len(chess_club["participants"]) == 2


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "signed up" in data["message"].lower()
    
    def test_signup_adds_participant(self, reset_activities):
        """Test that signup actually adds the participant"""
        student_email = "newstudent@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": student_email}
        )
        
        # Verify
        response = client.get("/activities")
        data = response.json()
        assert student_email in data["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, reset_activities):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Fake%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_duplicate_signup(self, reset_activities):
        """Test that duplicate signup returns error"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_full_activity(self, reset_activities):
        """Test signup for full activity returns error"""
        # First, fill a small activity (Tennis Club has 10 spots)
        for i in range(8):  # It already has 2, so 10 total
            activities["Tennis Club"]["participants"].append(f"student{i}@mergington.edu")
        
        # Now try to add another (should still work, max is 10)
        response = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": "extra1@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Add one more to reach max
        response = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": "extra2@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Now trying to add another should fail
        response = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": "extra3@mergington.edu"}
        )
        assert response.status_code == 400 or response.status_code == 409


class TestIntegration:
    """Integration tests for API workflows"""
    
    def test_signup_workflow(self, reset_activities):
        """Test complete signup workflow"""
        new_email = "testuser@mergington.edu"
        activity_name = "Chess Club"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        final_count = len(response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert new_email in response.json()[activity_name]["participants"]
    
    def test_multiple_activities(self, reset_activities):
        """Test user can sign up for multiple activities"""
        new_email = "versatile@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Art Studio"]
        
        # Sign up for multiple activities
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": new_email}
            )
            assert response.status_code == 200
        
        # Verify user is in all activities
        response = client.get("/activities")
        data = response.json()
        for activity in activities_to_join:
            assert new_email in data[activity]["participants"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
