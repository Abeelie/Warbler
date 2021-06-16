"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///test-warbler"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.user = User.signup("BOB", "bob@email.com", "password", None)
        self.user2 = User.signup("HOB", "hob@email.com", "password", None)

        db.session.commit()

        self.user_id = 200
        self.user.id = self.user_id
        self.user2_id = 201
        self.user2.id = self.user2_id

        user = User.query.get(self.user.id)
        user2 = User.query.get(self.user2.id)

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    def test_user_follows(self):
        self.assertEqual(len(self.user2.followers), 0)
        self.assertEqual(len(self.user.following), 0)
        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user.followers), 0)


  # Signup Tests


    def test_valid_signup(self):
        new_user = User.signup("Bobby", "Bob@Bob.com", "password", None)
        uid = 8000
        new_user.id = uid
        db.session.commit()

        new_user = User.query.get(uid)
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.username, "Bobby")
        self.assertEqual(new_user.email, "Bob@Bob.com")
        self.assertNotEqual(new_user.password, "password")
        self.assertTrue(new_user.password.startswith("$2b$"))


    def test_invalid_username_signup(self):
        invalid_username = User.signup(None, "Bob@Bob.com", "password", None)
        uid = 11
        invalid_username.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_invalid_email_signup(self):
        invalid_email = User.signup("Bob", None, "password", None)
        uid = 10
        invalid_email.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("Bob", "Bob@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("Bob", "Bob@email.com", None, None)
    

    # Authentication Tests
  
    def test_valid_authentication(self):
        u = User.authenticate(self.user.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(self.user.id, self.user_id)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.user.username, "badpassword"))
