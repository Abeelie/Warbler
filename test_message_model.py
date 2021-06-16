import os
from app import app
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///test-warbler"


db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()

        self.user_id = 10
        new_user = User.signup("testing", "testing@test.com", "password", None)
        new_user.id = self.user_id
        db.session.commit()

        self.new_user = User.query.get(self.user_id)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_message_model(self):
        new_message = Message(text="message", user_id=self.user_id)

        db.session.add(new_message)
        db.session.commit()

        self.assertEqual(len(self.new_user.messages), 1)
        self.assertEqual(self.new_user.messages[0].text, "message")


    def test_message_likes(self):
        new_message_1 = Message(text="message", user_id=self.user_id)
        new_message_2 = Message(text="another message", user_id=self.user_id)

        new_user = User.signup("BOB", "BOB@email.com", "password", None)
        user_id = 20
        new_user.id = user_id
        db.session.add_all([new_message_1, new_message_2, new_user])
        db.session.commit()

        new_user.likes.append(new_message_1)

        db.session.commit()

        total = Likes.query.filter(Likes.user_id == user_id).all()
        self.assertEqual(len(total), 1)
        self.assertEqual(total[0].message_id, new_message_1.id)


        