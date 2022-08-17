"""
Make userpages and make username restrictions using len() and regex. password only len() restriction.
maybe make post restrictions also
making userpage 
made comment ID. make so that post is saved in db only 1 time (now 2 in data and users). User pages should get data from "data" key. "users" key only must have comment id
"""

from replit import db
import secrets, time, random, json
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

def verify_session(request):
  return db["session"].get(request.cookies.get("session"))

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
db["data"] = []
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
  if verify_session(request):
    return redirect("/home")
  else:
    return redirect("/login")

@app.route('/home', methods=["GET","POST"])
def homepage():
  if not verify_session(request):
    return redirect("/login")
  if request.method == "POST":
    if request.form.get("purge") == "on":
      db["data"] = []
      for item in db["users"].keys():
        db["users"][item]["posts"] = []
    else:
      comments = db["data"]
      user = db["session"][request.cookies["session"]]
      with open("id.txt","r") as file:
        commentid = int(file.read()) + 1
      with open("id.txt", "w") as file:
        file.write(str(commentid))
      comment = {"id": commentid, "comment": {
        "username": user,
        "content": request.form["content"]
      }}
      comments.append(comment)
      db["users"][user.lower()]["posts"].append(commentid)
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
      db["login"][request.form["user"].lower()] = hashit(request.form["pass"])#setup user
      session = create_session()
      db["session"][session] = request.form["user"]
      db["users"][request.form["user"].lower()] = {"name": request.form["user"], "joined": int(time.time()), "bio": "", "posts":[]}
      return respond("session",session,"/home",30*24*60*60)
  msg = request.cookies.get("msg")
  res = make_response(render_template("signup.html",msg=msg))
  res.set_cookie("msg","",expires=0) #delete cookie
  return res #don't use respond as not redirecting...

@app.route("/users/<user>")
def userpage(user):
  if db["users"].get(user.lower()):
    posts = []
    with open("postlist.json", "w") as file:
      file.write(json.dumps(json.loads(db.get_raw("users"))[user.lower()]["posts"], indent=2))
    postlist = db["users"][user.lower()]["posts"]
    for item in db["data"]:
      if item["id"] in postlist:
        posts.append(item)
    posts.reverse()#new posts on top
    return render_template("user.html", user=db["users"][user.lower()], posts=posts)
  else:
    return f"User {user} doesn't exist..."


app.run(host='0.0.0.0', port=8080)
