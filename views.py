from datetime import datetime
from flask import current_app, render_template, request, redirect, url_for, flash, abort
from flask_login.utils import login_required
from movie import Movie, MovieNew
from person import Person
from passlib.hash import pbkdf2_sha256 as hasher
from user import get_user, User
from forms import LoginForm, SignupForm
from flask_login import login_user, logout_user, current_user
import os
import re



def home_page():
    """today = datetime.today()
    day_name = today.strftime("%A")
    return render_template("home.html", day=day_name)"""
    db = current_app.config["db"]
    if request.method == "GET":
        return render_template("movies_search.html")
    else:
        print("\nRead Form:")
        title = request.form["title"]
        print(title)
        score = request.form["score"]
        print(score)
        lang = request.form["answer"]
        print(lang)
        genres = request.form.getlist("genres")
        print(genres)

        movies = db.search_movie(title, score, lang, genres)
        return render_template("search.html", movies=movies) 

def profile_page():
    db = current_app.config["db"]
    username = current_user.username
    user = db.get_user(username)

    if not user.file_extension is None:
        folder = os.path.join('static', 'pps')
        full_filename = os.path.join(folder, str(username) + user.file_extension)
    else:
        full_filename = os.path.join('static', 'empty.png')

    return render_template("profile.html", user=user, image=full_filename)

def delete_profile_page():
    db = current_app.config["db"]
    username = current_user.username
    logout_user()
    db.delete_user(username)

    return redirect(url_for("home_page"))

@login_required
def add_movie_new_page():
    if not current_user.is_admin:
        abort(401)
    else:
        if request.method == "GET":
            values = {"title": "", "year": "", "avg_vote": ""}
            return render_template(
                "add_movie.html",
                values=values,
            )
        else:
            valid = validate_movie_form_new(request.form)
            if not valid:
                return render_template(
                    "add_movie.html",
                    min_year=1887,
                    max_year=datetime.now().year,
                    values=request.form,
                    min_score = 0,
                    max_score = 10
                )
            title = request.form.data["title"]
            year = request.form.data["year"]
            avg_vote = request.form.data["avg_vote"]
            movie = MovieNew("", title, year, "", "", "", "", "", "Unknown", "", "", avg_vote, 0)
            db = current_app.config["db"]
            print(title,year,avg_vote)
            imdb_title_id = db.add_movie_new(movie)
            return redirect(url_for("movie_new", imdb_id = imdb_title_id))


def users_page():
    db = current_app.config["db"]
    users = db.get_all_users()
    images  = []
    contents = []

    for user in users:
        if not user.file_extension is None:
            folder = os.path.join('static', 'pps')
            full_filename = os.path.join(folder, str(user.username) + user.file_extension)
        else:
            full_filename = os.path.join('static', 'empty.png')
        
        images.append(full_filename)

    for i in range(len(images)):
        contents.append((users[i], images[i]))


    return render_template("users.html", contents = contents)


def movies_page():
    db = current_app.config["db"]
    if request.method == "GET":
        movies = db.get_movies()
        return render_template("movies.html", movies=sorted(movies))
    else:
        if not current_user.is_admin:
            abort(401)
        form_movie_keys = request.form.getlist("movie_keys")
        for form_movie_key in form_movie_keys:
            db.delete_movie(int(form_movie_key))
        return redirect(url_for("movies_page"))


def movie_page(movie_key):
    db = current_app.config["db"]
    movie = db.get_movie(movie_key)
    return render_template("movie.html", movie=movie, movie_key = movie_key)

def movie_new(imdb_id):
    db = current_app.config["db"]
    movie = db.get_movie_new(imdb_id)
    return render_template("movie_new.html", movie=movie, imdb_id=imdb_id)

def delete_movie_page(imdb_title_id):
    db = current_app.config["db"]
    db.delete_movie_new(imdb_title_id)
    return redirect(url_for("home_page"))
    

@login_required
def update_avg_vote_page(imdb_title_id):
    if not current_user.is_admin:
        abort(401)
    else:
        db = current_app.config["db"]
        movie = db.get_movie_new(imdb_title_id)

        if request.method == "GET":
            values = {"avg_vote": ""}
            return render_template(
                "update_avg_vote.html",
                values=values,
                movie=movie
            )
        else:
            valid = validate_score_form(request.form)
            if not valid:
                return render_template(
                    "update_avg_vote.html",
                    values=request.form,
                    min_score = 0,
                    max_score = 10,
                    movie=movie
                )
            avg_vote = request.form.data["avg_vote"]
            db.update_avg_vote(imdb_title_id, avg_vote)
            return redirect(url_for("movie_new", imdb_id = imdb_title_id))

def casting_page(imdb_id):
    db = current_app.config["db"]
    persons = db.get_persons(imdb_id)
    movie = db.get_movie_new(imdb_id)
    return render_template("casting_page.html", imdb_id = imdb_id, movie_name = movie.original_title, persons = persons)

def person_page(imdb_name_id):
    db = current_app.config["db"]
    person = db.get_person(imdb_name_id)
    return render_template("person.html", person = person)

@login_required
def movie_add_page():
    if not current_user.is_admin:
        abort(401)
    if request.method == "GET":
        if request.method == "GET":
            values = {"title": "", "year": ""}
            return render_template(
                "movie_add.html",
                values=values,
            )
    else:
        valid = validate_movie_form(request.form)
        if not valid:
            return render_template(
                "movie_add.html",
                min_year=1887,
                max_year=datetime.now().year,
                values=request.form,
            )
        title = request.form.data["title"]
        year = request.form.data["year"]
        movie = Movie(title, year=year)
        db = current_app.config["db"]
        movie_key = db.add_movie(movie)
        return redirect(url_for("movie_page", movie_key=movie_key))

@login_required
def movie_edit_page(movie_key):
    db = current_app.config["db"]
    movie = db.get_movie(movie_key)

    if request.method == "GET":
        if request.method == "GET":
            values = {"title": "", "year": ""}
            return render_template(
                "movie_edit.html",
                values=values,
                movie_key=movie_key,
                movie=movie,
            )
    else:
        valid = validate_movie_form(request.form)
        if not valid:
            return render_template(
                "movie_edit.html",
                min_year=1887,
                max_year=datetime.now().year,
                values=request.form,
            )
        title = request.form.data["title"]
        year = request.form.data["year"]
        movie = Movie(title, year=year)
        db = current_app.config["db"]
        db.update_movie(movie_key, movie)
        return redirect(url_for("movie_page", movie_key=movie_key))

@login_required
def bio_page():
    db = current_app.config["db"]
    
    if request.method == "GET":
        values = {"bio": ""}
        return render_template("bio.html", values = values)
    else:
        valid = validate_bio_form(request.form)
        if not valid:
            return render_template("bio.html", values = request.form)
        
        bio = request.form.data["bio"]
        db.update_bio(current_user.username, bio)
        return(redirect(url_for("profile_page")))

def validate_bio_form(form):
    form.data = {}
    form.errors = {}

    form_bio = form.get("bio")
    print(len(form_bio))

    if len(form_bio) > 240:
        form.errors["bio"] = "Bio can not be longer than 240 characters."
    else:
        form.data["bio"] = form_bio

    return len(form.errors) == 0


def validate_movie_form(form):
    form.data = {}
    form.errors = {}

    form_title = form.get("title", "").strip()
    if len(form_title) == 0:
        form.errors["title"] = "Title can not be blank."
    else:
        form.data["title"] = form_title

    form_year = form.get("year")
    if not form_year:
        form.data["year"] = None
    elif not form_year.isdigit():
        form.errors["year"] = "Year must consist of digits only."
    else:
        year = int(form_year)
        if (year < 1887) or (year > datetime.now().year):
            form.errors["year"] = "Year not in valid range."
        else:
            form.data["year"] = year

    return len(form.errors) == 0



def validate_movie_form_new(form):
    form.data = {}
    form.errors = {}

    form_title = form.get("title", "").strip()
    #form_director = form.get("director", "").strip()
    if len(form_title) == 0:
        form.errors["title"] = "Title can not be blank."
    else:
        form.data["title"] = form_title
    

    form_avg_vote = form.get("avg_vote")
    if not form_avg_vote:
        form.data["avg_vote"] = 0
    elif (not form_avg_vote.isdigit()) and (re.match(r'^-?\d+(?:\.\d+)$', str(form_avg_vote)) is None):
        form.errors["avg_vote"] = "Average Vote must consist of digits only."
    else:
        avg_vote = float(form_avg_vote)
        if (avg_vote < 0) or (avg_vote > 10):
            form.errors["avg_vote"] = "Average vote not in valid range."
        else:
            form.data["avg_vote"] = avg_vote

    form_year = form.get("year")
    if not form_year:
        form.data["year"] = None
    elif not form_year.isdigit():
        form.errors["year"] = "Year must consist of digits only."
    else:
        year = int(form_year)
        if (year < 1887) or (year > datetime.now().year):
            form.errors["year"] = "Year not in valid range."
        else:
            form.data["year"] = year

    return len(form.errors) == 0


def validate_score_form(form):
    form.data = {}
    form.errors = {}

    form_avg_vote = form.get("avg_vote")
    if not form_avg_vote:
        form.data["avg_vote"] = 0
    elif (not form_avg_vote.isdigit()) and (re.match(r'^-?\d+(?:\.\d+)$', str(form_avg_vote)) is None):
        form.errors["avg_vote"] = "Average Vote must consist of digits only."
    else:
        avg_vote = float(form_avg_vote)
        if (avg_vote < 0) or (avg_vote > 10):
            form.errors["avg_vote"] = "Average vote not in valid range."
        else:
            form.data["avg_vote"] = avg_vote

    return len(form.errors) == 0



def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.data["username"]
        user = get_user(username)
        if user is not None:
            password = form.data["password"]
            if hasher.verify(password, user.password):
                login_user(user)
                flash("You have logged in.")
                next_page = request.args.get("next", url_for("home_page"))
                return redirect(next_page)
        flash("Invalid credentials.")
    return render_template("login.html", form=form)


def logout_page():
    logout_user()
    flash("You have logged out.")
    return redirect(url_for("home_page"))

def signup_page():
    form = SignupForm()
    db = current_app.config["db"]
    if form.validate_on_submit():
        username = form.data["username"]
        search_user = get_user(username)
        if search_user is not None:
            flash("Username taken.")
        else:
            password = form.data["password"]
            if len(password) < 5:
                flash("Password must be longer than 5 characters.")
            else:
                hashed_password = hasher.hash(password)
                db.insert_user(username, hashed_password)
                user_ = User(username, password, None, None)
                flash("You have signed up and logged in.")
                login_user(user_)
                next_page = request.args.get("next", url_for("home_page"))
                return redirect(next_page)
    return render_template("signup.html", form=form)


"""def movies_new_page():
    db = current_app.config["db"]
    if request.method == "GET":
        return render_template("movies_search.html")
    else:
        print("\nRead Form:")
        title = request.form["title"]
        print(title)
        score = request.form["score"]
        print(score)
        lang = request.form["answer"]
        print(lang)
        genres = request.form.getlist("genres")
        print(genres)

        movies = db.search_movie(title, score, lang, genres)

        return render_template("search.html", movies=movies) 
        #return redirect(url_for("search_movies_page",movies=movies))"""


def search_movies_page(movies):
    #print("----")
    #print(len(movies))
    return render_template("search.html", movies=movies) 



@login_required
def upload_page():
    db = current_app.config["db"]
    if request.method == "GET":
        #print("hey")

        #db = current_app.config["db"]
        #db.write_blob(1, "ok.jpg", "jpg")
        #db.read_blob(1, "uploads/")
        #db.write_pp("admin", "/uploads/empty.png")
        #db.read_pp("admin", "uploads/")
        #print("done")
        return render_template("file_upload.html")
    else:
        uploaded_file = request.files['file']
        extensions = ['.jpg', '.png', '.gif']
        #max_length = 1024*1024
        path = 'uploads' 
        """current_directory = os.getcwd()
        print(current_directory)
        db = Database(os.path.join(current_directory, "database.sqlite"))
        app.config["db"] = db"""
        if uploaded_file.filename != '':
            filename = uploaded_file.filename
            #print(uploaded_file.size)
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in extensions:
                abort(400)
            print(uploaded_file.filename)
            uploaded_file.save(os.path.join(path, uploaded_file.filename))
            username = current_user.username
            db.write_pp(str(username), os.path.join(path, uploaded_file.filename), file_ext)
        return redirect(url_for("profile_page"))






