import sqlite3
from flask import Flask, jsonify, send_from_directory, request, g
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

DATABASE = "movies.db"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()



print("Flask app is starting up...")




@app.get("/api")
def api_hello():
    db = get_db()
    return jsonify({"message": "Movies API"})

@app.route("/movies", methods=["GET"])
def list_movies():
    """
    List all movies

    ---

    responses:
        200:
            description: A list of movies
    """
    db = get_db()
    db.row_factory = sqlite3.Row

    director = request.args.get("director")

    if director is None:
        rows = db.execute(
            "SELECT id, title, year FROM movies"
        ).fetchall()
    else:
        # for now, we’ll just filter by director_id as a string param
        rows = db.execute(
            "SELECT id, title, year FROM movies WHERE director_id = ?",
            (director,)
        ).fetchall()

    movies_list = [dict(row) for row in rows]
    return jsonify(movies_list)



@app.route("/", methods=["GET"])
def home():
    return send_from_directory(".", "index.html")

@app.route("/movies/<int:id>", methods=["GET"])
def get_movie(id):
    """
    Get a single movie by its ID
    ---
    """
    db = get_db()
    db.row_factory = sqlite3.Row

    row = db.execute(
        "SELECT id, title, year FROM movies WHERE id = ?",
        (id,)
    ).fetchone()

    if row is None:
        return jsonify({
            "error": "not_found",
            "message": f"Movie with id {id} was not found."
        }), 404

    movie = dict(row)
    return jsonify(movie)

@app.route("/movies/<int:id>/full", methods=["GET"])
def get_full_movie(id):
    """
    Get a movie plus its director info
    """
    db = get_db()
    db.row_factory = sqlite3.Row

    row = db.execute(
        """
        SELECT
            movies.id AS id,
            movies.title AS title,
            movies.year AS year,
            directors.id AS director_id,
            directors.name AS director_name
        FROM movies
        INNER JOIN directors
            ON movies.director_id = directors.id
        WHERE movies.id = ?
        """,
        (id,)
    ).fetchone()

    if row is None:
        return jsonify({
            "error": "not_found",
            "message": f"Movie with id {id} was not found."
        }), 404

    full_movie = dict(row)
    return jsonify(full_movie)

@app.route("/movies", methods=["POST"])
def create_movie():
    body = request.get_json(silent=True)
    if body is None or not isinstance(body, dict):
        return jsonify({
            "error": "bad_request",
            "message": "Request body must be valid JSON."
        }), 400
    title = body.get("title")
    director_id = body.get("director_id")
    year = body.get("year")
    rating = body.get("rating")

    if title is None or director_id is None:
        return jsonify({
            "error": "bad_request",
            "message": "Fields 'title' and 'director_id' are required."
        }),400
    
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO movies (title, year, rating, director_id) VALUES (?, ?, ?, ?)",
            (body["title"], body["year"], body["rating"], body["director_id"])
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        return jsonify({
            "error": "Movie conflict",
            "message": str(e),
        }), 409
    
    new_movie ={
        "id": cursor.lastrowid,
        "title": title,
        "year": year,
        "rating": rating,
        "director_id": director_id
    }
    return jsonify(new_movie), 201
    

    
@app.route("/movies/<int:movie_id>/feedback", methods=["POST"])
def add_movie_feedback(movie_id):
        """
    Submit feedback for a movie

    ---
    parameters:
      - name: movie_id
        in: path
        type: integer
        required: true
        description: ID of the movie

      - in: body
        name: feedback
        required: true
        schema:
          type: object
          required:
            - thumb
          properties:
            thumb:
              type: string
              enum: [up, down]
            comment:
              type: string

    responses:
      201:
        description: Feedback submitted successfully
      400:
        description: Invalid feedback
      404:
        description: Movie not found
    """
        body = request.get_json()

        movie = next((m for m in movies if m["id"] == movie_id), None)

        if movie is None:
            return jsonify({
                "error": "not_found",
                "message": f"Movie with id {movie_id} was not found."

            }), 404

        if body is None:
            return jsonify({
                "error": "bad_request",
                "message": "Request body must be valid JSON."
            }), 400
        thumb = body.get("thumb")
        comment = body.get("comment")

        if thumb is None:
            return jsonify({
                "error": "bad_request",
                "message": "Field 'thumb' is required and must be 'up' or 'down'"
            }), 400
    
        if thumb not in ["up", "down"]:
            return jsonify({
                "error": "bad_request",
                "message": "Field 'thumb' must be either 'up' or 'down'."
            }), 400
    
        if comment is not None and not isinstance(comment, str):
            return jsonify({
                "error": "bad_request",
                "message": "Field 'comment' must be a string if provided."
            }), 400
    
        if "feedback" not in movie:
            movie["feedback"] = []

        feedback = {
            "thumb": body.get("thumb"),
            "comment": body.get("comment")
        }

        movie["feedback"].append(feedback)

        return jsonify(movie), 201
    



@app.route("/movies/<int:id>", methods=["PUT"])
def update_movie(id):
    db = get_db()
    body = request.get_json(silent=True)
    if body is None or not isinstance(body,dict):
        return jsonify({
            "error": "bad_request",
            "message": "Request body must be valid JSON."
        }), 400
    cursor = db.execute(
        "UPDATE movies SET title = ?, year = ?, rating = ?, director_id = ? WHERE id = ?",
        (body.get("title"), body.get("year"), body.get("rating"), body.get("director_id"), id)
    )
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({
            "error": "not_found",
            "message": f"Movie with id {id} was not found."
        }), 404
    return "",204
    

@app.route('/movies/<int:id>', methods=["DELETE"])
def delete_movie(id):
    db = get_db()
    cursor = db.execute("DELETE FROM movies WHERE id = ?", (id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({
            "error": "not_found",
            "message": f"Movie with id {id} was not found."
        }), 404
    return "", 204
if __name__ == "__main__":
    app.run(debug=True, port=5000)