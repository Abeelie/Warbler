"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///test-warbler"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.user = User.signup(username="BOB",
                                    email="BOB@BOB.com",
                                    password="password",
                                    image_url=None)

        self.user_id = 50
        self.user.id = self.user_id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")



    def test_add_no_session(self):
        with self.client as do:
            resp = do.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


    def test_add_invalid_user(self):
        with self.client as do:
            with do.session_transaction() as current:
                current[CURR_USER_KEY] = "200"

            resp = do.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    
    def test_message_show(self):

        new_message = Message(id=1234, text="message", user_id=self.user_id)
        
        db.session.add(new_message)
        db.session.commit()

        with self.client as do:
            with do.session_transaction() as current:
                current[CURR_USER_KEY] = self.user.id
            
            get_message = Message.query.get(1234)

            resp = do.get(f'/messages/{get_message.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(get_message.text, str(resp.data))


    def test_message_delete(self):

        delete_message = Message(id=1234, text="message", user_id=self.user_id)
        db.session.add(delete_message)
        db.session.commit()

        with self.client as do:
            with do.session_transaction() as current:
                current[CURR_USER_KEY] = self.user.id

            resp = do.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            get_message = Message.query.get(1234)
            self.assertIsNone(get_message)


    def test_message_delete_no_authentication(self):

        message = Message(id=1234, text="message", user_id=self.user_id)
        db.session.add(message)
        db.session.commit()

        with self.client as do:
            resp = do.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            message = Message.query.get(1234)
            self.assertIsNotNone(message)

