import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///test-warbler"

app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class MessageViewTestCase(TestCase):
	"""Test views for messages."""

	def setUp(self):
		"""Create test client"""

		db.drop_all()
		db.create_all()

		self.client = app.test_client()

		self.user = User.signup(username="BOB",
									email="BOB@bob.com",
									password="bob1bob2",
									image_url=None)
		self.user2 = User.signup(username="HOB",
									email="HOB@hob.com",
									password="hob1hob2",
									image_url=None)

		self.user_id = 200
		self.user.id = self.user_id
		self.user2_id = 201
		self.user2.id = self.user2_id

		db.session.commit()


	def tearDown(self):
		resp = super().tearDown()
		db.session.rollback()
		return resp


	def test_users_username(self):
		resp = self.client.get("/users")
		self.assertIn("@BOB", str(resp.data))
		self.assertIn("@HOB", str(resp.data))
	
	
	def test_users_in_search_bar(self):
		resp = self.client.get("/users?q=")
		self.assertIn("@BOB", str(resp.data))
		self.assertIn("@HOB", str(resp.data))


	def test_show_user(self):
		resp = self.client.get(f"/users/{self.user_id}")
		self.assertEqual(resp.status_code, 200)
		self.assertIn("@BOB", str(resp.data))


	def test_add_likes(self):
		message = Message(id=121, text="The open sea", user_id=self.user2_id)
		like = Likes(user_id=self.user_id, message_id=121)

		db.session.add(message)
		db.session.commit()

		db.session.add(like)
		db.session.commit()

		resp = self.client.post("/messages/1/like", follow_redirects=True)
		self.assertEqual(resp.status_code, 200)

		likes = Likes.query.filter(Likes.message_id==121).all()
		self.assertEqual(len(likes), 1)



	def test_unauthenticated_like(self):
		message = Message(id=121, text="The open sea", user_id=self.user2_id)
		like = Likes(user_id=self.user_id, message_id=121)

		db.session.add(message)
		db.session.commit()

		db.session.add(like)
		db.session.commit()

		mess = Message.query.filter(Message.text=="The open sea").one()
		self.assertIsNotNone(mess)

		like_count = Likes.query.count()

		
		resp = self.client.post(f"/messages/{mess.id}/like", follow_redirects=True)
		self.assertEqual(resp.status_code, 200)

		self.assertIn("Access unauthorized", str(resp.data))

		self.assertEqual(like_count, Likes.query.count())


	def setup_followers(self):
		ex1 = Follows(user_being_followed_id=self.user2_id, user_following_id=self.user_id)
		ex2 = Follows(user_being_followed_id=self.user_id, user_following_id=self.user2_id)

		db.session.add_all([ex1,ex2])
		db.session.commit()


	def test_show_following(self):

		self.setup_followers()
		with self.client as do:
			with do.session_transaction() as sess:
				sess[CURR_USER_KEY] = self.user_id

			resp = do.get(f"/users/{self.user_id}/following")
			self.assertEqual(resp.status_code, 200)
			self.assertIn("@BOB", str(resp.data))


	def test_show_followers(self):

		self.setup_followers()
		with self.client as do:
			with do.session_transaction() as sess:
				sess[CURR_USER_KEY] = self.user_id

			resp = do.get(f"/users/{self.user_id}/followers")

			self.assertIn("@BOB", str(resp.data))


	def test_unauthorized_following_page_access(self):
		self.setup_followers()
		with self.client as do:

			resp = do.get(f"/users/{self.user_id}/following", follow_redirects=True)
			self.assertEqual(resp.status_code, 200)
			self.assertNotIn("@HOB", str(resp.data))
			self.assertIn("Access unauthorized", str(resp.data))

	def test_unauthorized_followers_page_access(self):
		self.setup_followers()
		with self.client as do:

			resp = do.get(f"/users/{self.user_id}/followers", follow_redirects=True)
			self.assertEqual(resp.status_code, 200)
			self.assertNotIn("@HOB", str(resp.data))
			self.assertIn("Access unauthorized", str(resp.data))
