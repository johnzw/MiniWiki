from google.appengine.ext import db


class User(db.Model):
	"""docstring for Art"""
	#constraints
	username = db.StringProperty(required=True)
	password = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	email = db.EmailProperty()

	@classmethod
	def fetchByName(cls, username):
		return db.GqlQuery("select * from User Where username='%s'" % username)

class Blog(db.Model):
	"""docstring for Blog"""
	#constraints
	title = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)

class Page(db.Model):
	title = db.StringProperty()
	content = db.TextProperty()
	created = db.DateTimeProperty(auto_now_add=True)

	@classmethod
	def fetchPages(cls, title):
		return db.GqlQuery("select * from Page Where title='%s' ORDER By created DESC" % title)
		
