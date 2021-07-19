from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
MOVIE_DB_API_KEY = os.getenv('API_KEY')
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_DETAILS_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMG_URL = "https://image.tmdb.org/t/p/w500"
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///my-movie-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


class RateMovieForm(FlaskForm):
    new_rating = StringField(label='Your Rating Out of 10 e.g 7.5', validators=[DataRequired()])
    new_review = StringField(label='Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddMovieForm(FlaskForm):
    movie_title = StringField(label='Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


db.create_all()


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth,"
#                 " pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, "
#                 "Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()


@app.route("/")
def home():
    # creates and sorts lists of movies in db sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", all_movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    add_movie_form = AddMovieForm()
    raw_data = {}
    if add_movie_form.validate_on_submit():
        added_movie = add_movie_form.movie_title.data
        response = requests.get(url=MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": added_movie}).json()
        results = response['results']
        for n in range(len(results)):
            raw_data[n] = {
                "title": results[n]['title'],
                "year": results[n]['release_date'].split('-')[0],
                "id": results[n]['id'],
            }
        data = [raw_data[i] for i in range(len(raw_data))]
        return render_template('select.html', data=data)

    return render_template('add.html', add_movie_form=add_movie_form)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    movie_title = request.args.get('_title')
    rate_movie_form = RateMovieForm()
    if rate_movie_form.validate_on_submit():
        _id = request.args.get('_id')
        movie_to_update = Movie.query.get(_id)
        movie_to_update.review = rate_movie_form.new_review.data
        movie_to_update.rating = rate_movie_form.new_rating.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit.html', edit_form=rate_movie_form, movie_title=movie_title)


@app.route("/details")
def get_movie():
    _id = request.args.get('_id')
    response = requests.get(url=f"{MOVIE_DB_DETAILS_URL}/{_id}", params={"api_key": MOVIE_DB_API_KEY}).json()
    movie_data = {
        "title": response['title'],
        "img_url": f"{MOVIE_DB_IMG_URL}{response['poster_path']}",
        "year": response['release_date'].split('-')[0],
        "description": response['overview'],
    }
    new_movie = Movie(
        title=movie_data['title'],
        year=movie_data['year'],
        description=movie_data['description'],
        img_url=movie_data['img_url']
    )
    db.session.add(new_movie)
    db.session.commit()
    db.session.flush()
    _id = new_movie.id

    return redirect(url_for('edit', _id=_id))


@app.route("/delete")
def delete():
    _id = request.args.get('_id')
    movie_to_delete = Movie.query.get(_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
