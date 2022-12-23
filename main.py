from replit import db
import secrets, time, random, re, string
from flask import Flask, render_template, request, redirect, make_response
from flask_bcrypt import Bcrypt

#db["users"]["testuser"] = {"name": "TestUser", "joined": int(time.time())-17282776, "bio": "a"*200, "status": (("b"*10)+"\n")*10, "posts":[], "following": list(string.ascii_lowercase), "followers": list(string.ascii_uppercase), "admin": False}
#exit()
app = Flask('app')
hash = Bcrypt(app)
regexuser = re.compile("^[A-Za-z0-9_-]{1,20}$")
regexpass = re.compile("^[A-Za-z0-9.:;!,-?+*_]{1,25}$")

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
  return regexuser.match(name)

def passvalid(passwo):
  return regexpass.match(passwo)

def postvalid(post):
  limit = 500
  if 0 < len(post) <= limit:
    return post
  elif len(post) > 0:
    return post[:limit]
  else:
    return False

def resetid():
  with open("id.txt","w") as file:
    file.write("0")

"""
def resetdb():
  db.clear()
  db["data"] = []
  db["login"] = {}
  db["users"] = {}
  db["session"] = {}
  resetid()
  exit()

resetdb()
#"""
@app.route("/", methods=["GET","POST"])
def mainpage():
  if verify_session(request):
    return redirect("/home")
  else:
    return redirect("/login")

@app.route('/home', methods=["GET","POST"])
def homepage():
  user = verify_session(request)
  if not user:
    return redirect("/login")
  if request.method == "POST":
    postcontent = postvalid(request.form["content"].strip())
    if request.form.get("purge") == "on":
      db["data"] = []
      resetid()
      for item in db["users"].keys():
        db["users"][item]["posts"] = []
    elif postcontent:
      comments = db["data"]
      with open("id.txt","r") as file:
        commentid = int(file.read())
      with open("id.txt", "w") as file:
        file.write(str(commentid+1))
      comment = {
        "id": commentid,
        "username": db["users"][user.lower()]["name"],
        "content": postcontent
      }
      comments.append(comment)
      db["users"][user.lower()]["posts"].append(commentid)
      db["data"] = comments
    return redirect("/home")
  else:
    pass
  comments = db["data"][:]
  comments.reverse()
  return render_template("index.html", data = comments, user = db["users"][user.lower()])

@app.route("/login", methods=["GET","POST"])
def loginpage():
  if request.method == "POST":
    if not db["login"].get(request.form["user"].lower()):
      return respond("msg","User doesnt exist","/login")
    if compareit(db["login"][request.form["user"].lower()], request.form["pass"]):
      session = create_session()
      db["session"][session] = request.form["user"].lower()
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

    if not (namevalid(request.form["user"]) and passvalid(request.form["pass"])):
      return respond("msg", "Username and password length must be less than 21 and only containing characters: A-Z, a-z, _, -. Passwords can have additional chars: .:;!-?,+*_", "/signup")
    
    if db["login"].get(request.form["user"].lower()):
      return respond("msg", "name already exists", "/signup")
    else:
      db["login"][request.form["user"].lower()] = hashit(request.form["pass"])#setup user
      session = create_session() #CREATION HERE
      db["session"][session] = request.form["user"].lower()
      db["users"][request.form["user"].lower()] = {"name": request.form["user"], "joined": int(time.time()), "bio": "", "status": "", "posts":[], "following": [], "followers": [], "admin": False}
      return respond("session",session,"/home",30*24*60*60)
  msg = request.cookies.get("msg")
  res = make_response(render_template("signup.html",msg=msg))
  res.set_cookie("msg","",expires=0) #delete cookie
  return res #don't use respond as not redirecting...

@app.route("/users/<user>", methods = ["GET", "POST"])
def userpage(user):
  username = verify_session(request)
  if not username:
    return redirect("/login")

  selfprofile =  (user.lower() == username.lower()) #check whether his own profile is requested
 
  
  if request.method == "POST":
    bio = request.form["bio"]
    status = request.form["status"]
    if len(bio) > 100 or len(status) > 100:
      bio = bio[:100]
      status = status[:100]
    db["users"][username.lower()].update(bio=bio, status=status) #update multiple keys at once
    return "Done the post req. anyway Noone reading the response"

  if db["users"].get(user.lower()):
    posts = []
    follow = "follow"
    following = db["users"][user.lower()]["following"]
    selffollowing= db["users"][username.lower()]["following"]
    if user.lower() in selffollowing:
      follow = "unfollow"
    postlist = db["users"][user.lower()]["posts"][:] #not pointer which will change the original list. this just copies the list
    postlist.reverse()
    for item in postlist:
      posts.append(db["data"][item])

    return render_template("user.html", user=db["users"][user.lower()], posts=posts, follow = follow, following = following,  selfprofile = selfprofile)
  else:
    return render_template("404.html", msg= f"User {user} doesn't exist.")

@app.route("/follow")
def followpage():
  user = verify_session(request)
  print(request.args) #request args data already lowercase
  if request.args["follow"] in db["users"][user]["following"]:
    db["users"][user]["following"].remove(request.args["follow"])
  elif db["users"].get(request.args["follow"]):
    db["users"][user]["following"].append(request.args["follow"])
  return redirect("/users/"+request.args["follow"])


@app.route("/users")
def userlist():
  if request.args.get("q"):
    return redirect(f"/users/{request.args['q'].strip()}")
  return render_template("allusers.html", text=db["users"].keys())
  
@app.route("/logout")
def logoutpage():
  user = verify_session(request)
  if not user:
    return redirect("/login")
  return respond("session", "", "/login", 0)

@app.errorhandler(404)
def notfoundpage(error):
  return render_template("404.html")

app.run(host='0.0.0.0', port=8080)
