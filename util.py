import hmac
import random
import string
import hashlib

SECRET = "guess_what!"

def make_salt():
	return ''.join(random.choice(string.letters) for x in range(5))

def make_pw_hash(pw,salt=None):
	if salt== None:
		salt = make_salt()
	h = hashlib.sha256(pw+salt).hexdigest()
	return "%s|%s" % (h,salt)

def check_pw_hash(pw, h):
	salt = h.split("|")[1]
	return h == make_pw_hash(pw,salt)

def make_secure_val(s):
	hash_code = hmac.new(SECRET, s).hexdigest()
	return "%s|%s" % (s,hash_code)

def check_secure_val(h):
	val = h.split("|")[0]
	if h == make_secure_val(val):
		return val

