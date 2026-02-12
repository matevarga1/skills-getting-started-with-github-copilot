"""
Test suite for the Mergington High School API.
Tests cover activity retrieval, signup, and unregistration functionality.
"""

import pytest
from conftest import activities


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test that activities are returned successfully"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Science Club" in data
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_activities_count(self, client):
        """Test that the correct number of activities are returned"""
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9  # 9 activities in total


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post("/activities/Programming Class/signup", params={"email": email})
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        programming_class = activities_response.json()["Programming Class"]
        assert email in programming_class["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test that signup returns 404 for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_new_student_existing_activity(self, client, reset_activities):
        """Test that a new student can sign up for an activity with existing participants"""
        response = client.post(
            "/activities/Tennis Club/signup",
            params={"email": "newplayer@mergington.edu"}
        )
        
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        tennis_club = activities_response.json()["Tennis Club"]
        assert "newplayer@mergington.edu" in tennis_club["participants"]
        assert "sarah@mergington.edu" in tennis_club["participants"]  # Original participant


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "daniel@mergington.edu"  # In Chess Club
        client.delete("/activities/Chess Club/signup", params={"email": email})
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        chess_club = activities_response.json()["Chess Club"]
        assert email not in chess_club["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test that unregister returns 404 for non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_student_not_registered(self, client, reset_activities):
        """Test that unregister returns 400 if student is not registered"""
        response = client.delete(
            "/activities/Art Studio/signup",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_from_activity_with_multiple_participants(self, client, reset_activities):
        """Test unregistering from an activity that has multiple participants"""
        # Theatre Club has lucas and ava
        response = client.delete(
            "/activities/Theatre Club/signup",
            params={"email": "lucas@mergington.edu"}
        )
        
        assert response.status_code == 200
        
        # Verify only the targeted participant was removed
        activities_response = client.get("/activities")
        theatre_club = activities_response.json()["Theatre Club"]
        assert "lucas@mergington.edu" not in theatre_club["participants"]
        assert "ava@mergington.edu" in theatre_club["participants"]


class TestSignupAndUnregisterWorkflow:
    """Tests for combined signup and unregistration workflows"""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test signing up and then unregistering from an activity"""
        email = "workflow@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            "/activities/Gym Class/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        check_response = client.get("/activities")
        assert email in check_response.json()["Gym Class"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            "/activities/Gym Class/signup",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        final_check = client.get("/activities")
        assert email not in final_check.json()["Gym Class"]["participants"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test signing up for multiple activities"""
        email = "multiactivity@mergington.edu"
        
        # Sign up for multiple activities
        for activity in ["Chess Club", "Programming Class", "Art Studio"]:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify signup for all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]
        assert email in activities_data["Art Studio"]["participants"]
