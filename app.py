import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo= PyMongo(app)


@app.route("/")
@app.route("/get_books")
def get_books():
    books = list(mongo.db.books.find())
    return render_template("books.html", books=books)


@app.route("/home")
def home():
    book = mongo.db.books.aggregate([{"$sample": {"size": 1}}])
    return render_template("home.html", book=book)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    books = list(mongo.db.books.find({"$text": {"$search": query}}))
    return render_template("books.html", books=books)


@app.route("/profile_search", methods=["GET", "POST"])
def profile_search():
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    profile_query = request.form.get("profile_query")
    books = list(mongo.db.books.find({"$and": [{"$text": {"$search": profile_query}},
                                                {"created_by": username}]}))
    return render_template("profile.html", username=username, books=books)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        if request.form['password'] != request.form['confirm_password']:
                flash("Passwords do not match")
                return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Complete")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # if username exists then ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "home"))
            else:
                #invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # if username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # take the session user's username from the database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        books = list(mongo.db.books.find({"created_by": username}))
        return render_template("profile.html", username=username, books=books)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        book = {
            "book_title": request.form.get("book_title"),
            "book_author": request.form.get("book_author"),
            "genre": request.form.getlist("genre[]"),
            "rating":request.form.get("rating"),
            "book_description": request.form.get("book_description"),
            "created_by": session["user"],
            "book_cover": request.form.get("book_cover")
        }
        mongo.db.books.insert_one(book)
        flash("Book Review Successfully Added")
        return redirect(url_for("get_books"))

    return render_template("add_book.html")


@app.route("/edit_book/<book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if request.method == "POST":
        submit = {
            "book_title": request.form.get("book_title"),
            "book_author": request.form.get("book_author"),
            "genre": request.form.getlist("genre[]"),
            "rating":request.form.get("rating"),
            "book_description": request.form.get("book_description"),
            "created_by": session["user"],
            "book_cover": request.form.get("book_cover")
        }
        mongo.db.books.update_one({"_id": ObjectId(book_id)}, { "$set": submit })
        flash("Book Review Successfully Updated")

    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template("edit_book.html", book=book)


@app.route("/delete_book/<book_id>")
def delete_book(book_id):
    mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    flash("Book Review Successfully Deleted")
    return redirect(url_for("profile", username=session["user"]))

@app.route("/reviews/<book_id>", methods=["GET", "POST"])
def reviews(book_id):
    if request.method == "POST":
        comment = {
            "review_text": request.form.get("review_text"),
            "review_by": session["user"],
            "review_title": request.form.get("review_title"),
            "rating":request.form.get("rating")
        }
        mongo.db.reviews.insert_one(comment)
        flash("Your review has been successfully added")

    reviews = list(mongo.db.reviews.find())
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template("reviews.html", book=book, reviews=reviews)




if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)