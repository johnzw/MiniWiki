import os
import webapp2
import jinja2
import util
import datetime
import json
import re
from google.appengine.api import memcache
import logging
import datetime
from models import User, Blog, Page

#os.path.curdir,instead of os.path.
template_dir = os.path.join(os.path.curdir,'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
								autoescape = True)

#For template processing
class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template,**kw))

def top_blog(update=False):
	key="top"
	time_key='gen_time'

	blogs = memcache.get(key)

	if blogs is None or update:
		logging.error("DB QUERY")
		blogs = db.GqlQuery("select * from Blog ORDER By created DESC")

		blogs = list(blogs)
		memcache.set(key,blogs)

		#save into quried time into the memcache
		timestamp = datetime.datetime.now()
		memcache.set(time_key,timestamp)

	gen_timestamp = memcache.get(time_key)
	cur_timestamp = datetime.datetime.now()

	time_gap = (cur_timestamp - gen_timestamp).seconds
	
	return time_gap, blogs

class MainPage(Handler):
	"""docstring for MainPage"""
	def render_front(self):
		time_gap, blogs = top_blog()
		self.render("fronpage.html", time_gap=time_gap, blogs=blogs)
	
	def get(self):
		self.render_front()

def spec_blog(blog_id):
	
	blogs = memcache.get(blog_id)

	if not blogs:
		blog = Blog.get_by_id(int(blog_id))
		if blog:
			blogs =[blog]
			memcache.set(blog_id,blogs)
			timestamp = datetime.datetime.now()
			memcache.set('time|'+blog_id, timestamp)
		else:
			return None, None

	cur_timestamp = datetime.datetime.now()
	gen_timestamp = memcache.get('time|'+blog_id)
	time_gap = (cur_timestamp - gen_timestamp).seconds

	return time_gap, blogs

class PostHandler(Handler):
	"""docstring for PostHandler"""
	def get(self, blog_id):
		time_gap, blogs = spec_blog(blog_id)
		if blogs:
			self.render("fronpage.html", time_gap=time_gap, blogs=blogs)
		else:
			self.error(404)
			return


class PostPage(Handler):
	"""docstring for PostPage"""
	def render_front(self, title="", content="", error=""):
		self.render("post.html", title=title, content=content,error=error)
	
	def get(self):
		self.render_front()

	def post(self):
		title = self.request.get("subject")
		content = self.request.get("content")

		if title and content:
			blog = Blog(title=title,content=content)
			blog.put()
			

			blog_id = str(blog.key().id())
			top_blog(True)
			
			self.redirect("/blog/"+blog_id)
		else:
			error="subject and content, please!"
			self.render_front(error=error,title=title,content=content)

class EditPage(Handler):
	
	def render_front(self, username="",title="", content="", error=""):
		self.render("edit_user.html",username=username, title=title, content=content,error=error)
		
	def get(self, title):

		# check the user identity
		cookie_val = self.request.cookies.get('user_id')
		username = None
		#check whether it is login user
		if cookie_val:
			user_id = util.check_secure_val(cookie_val)
			if user_id:
				user_id = int(user_id)
				user = User.get_by_id(user_id)

				if user:
					username = user.username
				else:
					#punish the stupid hacker	
					self.error("404")
					return

		if username:
			# check whether the page has been created
			query = Page.fetchPages(title)
			page = query.fetch(1)

			if page:
				self.render_front(username=username,title=title,content=page[0].content)
			else:	
				self.render_front(username=username,title=title)
		else:
			self.redirect("/")

	def post(self, title):
		# check the user identity
		cookie_val = self.request.cookies.get('user_id')
		username = None
		#check whether it is login user
		if cookie_val:
			user_id = util.check_secure_val(cookie_val)
			if user_id:
				user_id = int(user_id)
				user = User.get_by_id(user_id)

				if user:
					username = user.username
				
		if username:

			content = self.request.get("content")

			if content:
				if len(str.strip(str(content))):
					#save to Page

					page = Page(title=title,content=content)
					page.put()
					
					self.redirect("/"+title)
			else:
				error="the content must not be empty"
				self.render_front(username=username,title=title,error=error,content=content)
		else:
			#punish the stupid hacker	
			self.error("404")
			return
		
class WikiPage(Handler):

	def get(self,title):
		#check user identity
		cookie_val = self.request.cookies.get('user_id')
		username = None
		#check whether it is login user
		if cookie_val:
			user_id = util.check_secure_val(cookie_val)
			if user_id:
				user_id = int(user_id)
				user = User.get_by_id(user_id)

				if user:
					username = user.username
					#punish the stupid hacker
				else:	
					self.error("404")
					return

		query = Page.fetchPages(title)
		page = query.fetch(1)
		# get to be done

		if username:
			if page:
				self.render("wikipage_user.html",username=username,title=title,content=page[0].content)
			else:
				self.redirect("/_edit/"+title)
		else:
			if page:
				self.render("wikipage_normal.html",content=page[0].content)
			else:
				self.write("<h1>Authentication Failed</h1>"\
							"<h1>GO BACK BOY!</h1>")

class HistoryPage(Handler):
	
	def get(self, title):
		
		
class LoginPage(Handler):
	def render_front(self,username="",password="",error=""):
		self.render("signin.html",username=username,
					password=password, error= error)
	
	def get(self):
		self.render_front()

	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")

		query = User.fetchByName(username)
		user = query.fetch(1)

		if user and util.check_pw_hash(password, user[0].password):
			#user login
			user_id = str(user[0].key().id())

			cookie = util.make_secure_val(user_id)
			self.response.headers.add_header('Set-Cookie','user_id=%s'%cookie)

			self.redirect("/")
		else:
			error="Invalid username or password"
			self.render_front(error= error, username= username, password= password)



class LogoutPage(Handler):
	def get(self):
		self.response.headers.add_header('Set-Cookie','user_id=;Path=/')
		self.redirect('/')

#deal with sign up request
class SignupPage(Handler):
	def render_front(self, username="", password="",verifypw="",email="",
					 error_username = "", error_password = "",
					 error_verifypw = "", error_email = ""):

		self.render("signup.html", username=username, password=password,
					verifypw = verifypw, email=email,
					error_username = error_username, error_password = error_password,
					error_verifypw = error_verifypw, error_email = error_email)
	
	def get(self):
		self.render_front()

	#following are 4 check functions
	def check_username(self,username):
		if not username:
			return "username shouldn't be blank"
		else:
			query = User.fetchByName(username)
			user = query.get()
			if user:
				return "username alread taken, please change to another one"

	def check_password(self,password):
		if not password:
			return "password shouldn't be blank"
		elif len(password)>20:
			return "password shouldn't be more than 20 characters"

	def check_verifypw(self,password, verifypw):
		if not password == verifypw:
			return "the password verified should be equeal to the one above"
	
	def check_email(self,email):
		if email:
			if not re.match("[^@]+@[^@]+\.[^@]+", email):
				return "Email address invalid"

	def post(self):
		#get all the parameters
		username = self.request.get("username")
		password = self.request.get("password")
		verifypw = self.request.get("verify")
		email = self.request.get("email")
		
		#process all the possible error
		error_username = self.check_username(username)
		error_password = self.check_password(password)
		error_verifypw = self.check_verifypw(password, verifypw)
		error_email = self.check_email(email)
		
		#print out the error
		if error_username:
			self.render_front(error_username=error_username)
		elif error_password:
			self.render_front(username = username, error_password = error_password)
		elif error_verifypw:
			self.render_front(username = username, password= password, error_verifypw = error_verifypw)
		elif error_email:
			self.render_front(username=username, password = password, verifypw = verifypw,
				error_email = error_email)
		else:
			#hash the password
			password = util.make_pw_hash(password)

			#everything is right on its way
			if email:

				user = User(username = username, password = password, email= email)
			else:
				user= User(username = username, password = password)
			
			#here should be some technique to prevent collision
			user.put()

			user_id = str(user.key().id())

			cookie = util.make_secure_val(user_id)
			self.response.headers.add_header('Set-Cookie','user_id=%s'%cookie)

			#redirect to the HomePage
			self.redirect("/")

class FlushHandler(Handler):
	def get(self):
		memcache.flush_all()
		self.redirect("/")
		
app = webapp2.WSGIApplication([('/flush',FlushHandler),
    							('/blog/newpost',PostPage),
    							('/blog',MainPage),
    							('/blog/([0-9]+)',PostHandler),
    							('/signup',SignupPage),
    							('/login',LoginPage),
    							('/logout',LogoutPage),
    							('/_edit/(\w*)',EditPage),
    							('/(\w*)',WikiPage)], 
    							debug=True)
