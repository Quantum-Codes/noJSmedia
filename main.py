"""writing line 114
Make userpages and make username restrictions using len() and regex. password only len() restriction.
maybe make post restrictions also
"""

from replit import db
import secrets, time, random
from flask import Flask, render_template, request, redirect, make_response
from flask_bcrypt import Bcrypt

app = Flask('app')
hash = Bcrypt(app)

def hashit(password):
  return hash.generate_password_hash(password).decode("utf8")

def compareit(hashed, password):
  return hash.check_password_hash(hashed, password)

def create_session():
  ses = f"{secrets.token_urlsafe(10)}{hex(int(time.time()))[2:]}{secrets.token_urlsafe(10)}{hex(random.randint(1000,9999999999))[2:]}"
  if db["session"].get(ses):
    ses = create_session()
  return ses

def respond(cookie, value, page, expire = 60):
  res = make_response(redirect(page))
  res.set_cookie(cookie, value, expires=int(time.time() + expire))
  return res

def namevalid(name):
  if len(name) < 21:
    return True
  else:
    return False

"""
db.clear()
db["data"] = "hi"
print(db["data"])
db["data"] = [
  {
    "username": "User1",
    "content": "First post yay",
    "id": 1
  }
]


db["login"] = {}
db["users"] = {}
db["session"] = {}
exit()
#"""
@app.route("/", methods=["GET","POST"])
def mainpage():
  if request.cookies.get("session"):
    return redirect("/home")
  else:
    return """<link rel="stylesheet" href="static/main.css"><a href="/login">replace to redirect to login</a>"""

@app.route('/home', methods=["GET","POST"])
def homepage():
  if not request.cookies.get("session"):
    return redirect("/login")
  if request.method == "POST":
    if request.form.get("purge") == "on":
      db["data"] = []
    else:
      comments = db["data"]
      comments.append({
        "username": db["session"][request.cookies["session"]],
        "content": request.form["content"],
        "id": 1
      })
      db["data"] = comments
      return redirect("/home")
  else:
    pass
  comments = db["data"]
  return render_template("index.html", data = comments)

@app.route("/login", methods=["GET","POST"])
def loginpage():
  if request.method == "POST":
    if not db["login"].get(request.form["user"].lower()):
      return respond("msg","User doesnt exist","/login")
    if compareit(db["login"][request.form["user"].lower()], request.form["pass"]):
      session = create_session()
      db["session"][session] = request.form["user"]
      return respond("session",session,"/home",30*24*60*60)
    else:
      return respond("msg","wrong credentials","/login")
  msg = request.cookies.get("msg")
  res = make_response(render_template("login.html",msg=msg))
  res.set_cookie("msg","",expires=0) #delete cookie
  return res #don't use respond as not redirecting...

@app.route("/signup", methods=["GET", "POST"])
def signuppage():
  if request.method == "POST":
    if not (request.form["user"] and request.form["pass"]):
      return respond("msg", "username/password can't be empty", "/signup")

    if not namevalid(request.form["user"]):
      return respond("msg", "Username length must be less than 21 and only containing characters: A-Z, a-z, _, -", "/signup")
    
    if db["login"].get(request.form["user"].lower()):
      return respond("msg", "name already exists", "/signup")
    else:
      db["login"][request.form["user"].lower()] = hashit(request.form["pass"])
      session = create_session()
      db["session"][session] = request.form["user"]
      db["users"][request.form["user"].lower()] = {"bio": "", "posts":[]}
      return respond("session",session,"/home",30*24*60*60)
  msg = request.cookies.get("msg")
  res = make_response(render_template("signup.html",msg=msg))
  res.set_cookie("msg","",expires=0) #delete cookie
  return res #don't use respond as not redirecting...

@app.route("/users/<user>")
def userpage(user):
  if db["users"].get(user.lower()):
    return f"I got the page. WIP {user}"
  else:
    return f"User {user} doesn't exist..."


app.run(host='0.0.0.0', port=8080)
