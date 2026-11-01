
from flask import Flask, jsonify, send_from_directory, request
from flasgger import Swagger # New 10/26/26

app = Flask(__name__)
swagger = Swagger(app) # New 10/26/26


print("Flask app is starting up...")

movies = [
    {
        "id": 1,
        "title": "Den of Thieves",
        "year": 2018,
        "director": "Christian Gudegast",
        "watched": True,
    },
    {
        "id": 2,
        "title": "Inception",
        "director": "Christopher Nolan",
        "year": 2010,
        "watched": True,
    },
    {
        "id": 3,
        "title": "Dune",
        "director": "Denis Villaneuve",
        "year": 2021,
        "watched": True,
    },
    {
        "id": 4,
        "title": "The Matrix",
        "director": "The Wachowskis",
        "year": 1999,
        "watched": False,
    },
]

next_id = 5

@app.route("/movies", methods=["GET"])
def list_movies():
    """
    List all movies

    ---

    responses:
        200:
            description: A list of movies
    """
    director = request.args.get("director")
    if director is None:
        result = movies
    else:
        result = [m for m in movies if m["director"] == director]
    return jsonify(result)



@app.route("/", methods=["GET"])
def home():
    return send_from_directory(".", "index.html")

@app.route("/movies/<int:id>", methods=["GET"])
def get_movie(id):
    """
    Get a single movie by its ID


    ---
    parameters:
       - name: id
         in: path
         type: integer
         required: true
         description: The ID of the movie

    responses:
        200:
           description: A single movie
        
        404:
           description: Movie not found

    """
    movie = next((m for m in movies if m["id"] == id), None)

    if movie is None:
        return jsonify({
            "error": "not_found",
            "message": f"Movie with id {id} was not found."
        }),404
    return jsonify(movie)

@app.route("/movies", methods=["POST"])
def create_movie():
    """
    Create a new movie

    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: movie
        required: true
        description: Movie to create
        schema:
          type: object
          properties:
            title:
              type: string
            director:
              type: string
            year:
              type: integer
            watched:
              type: boolean
            duration:
              type: integer
          required:
            - title
            - director
            - year
            - watched
            - duration

    responses:
      201:
        description: Movie created successfully
        schema:
          type: object
          properties:
            id:
             type: integer
            title:
              type: string
            director:
              type: string
            year:
              type: integer
            watched:
              type: boolean
            duration:
              type: integer
          required:
            - id
            - title
            - year
            - watched
            - duration

      400:
        description: Validation failed
        schema:
          type: object
          properties:
            error:
              type: string
              example: validation_failed
            message:
              type: string
          required:
            - error
            - message
    """
    global next_id

    body = request.get_json(silent=True) or {}

    required_fields = ["title", "director", "year", "watched", "duration"]

    for field in required_fields:
        if field not in body:
            return jsonify({
                "error": "validation_failed",
                "message": f"Missing required field: {field}"
            }), 400
    
    if not isinstance(body['year'], int):
        return jsonify({
            "error": "validation_failed",
            "message": "Field 'year' must be a number."
        }), 400

    if not isinstance(body["duration"], int):
        return jsonify({
            "error": "validation_failed",
            "message":"Field 'duration' must be a number(minutes)."
        }), 400

    if not isinstance(body["title"], str):
        return jsonify({
            "error": "validation_failed",
            "message": "Field 'title' must be a string."
        }), 400

    if not isinstance(body["director"], str):
        return jsonify({
            "error": "validation_failed",
            "message": "Field 'director' must be a string."
        }), 400

    if not isinstance(body["watched"], bool):
        return jsonify({
            "error": "validation_failed",
            "message": "Field 'watched' must be a boolean."
        }), 400

    new_movie = {
        "id": next_id,
        "title": body.get("title"),
        "director": body.get("director"),
        "year": body.get("year"),
        "watched": body.get("watched"),
        "duration": body.get("duration")
    }
    movies.append(new_movie)
    next_id += 1
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
        """
    Update an existing movie

    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID of the movie to update

      - in: body
        name: movie
        required: true
        description: Updated movie information
        schema:
          type: object
          properties:
            title:
              type: string
            director:
              type: string
            year:
              type: integer
            watched:
              type: boolean

    responses:
      200:
        description: Movie updated successfully

      404:
        description: Movie not found
    """
        body = request.get_json(silent=True) or {}

    #1. find the exisiting movie with this id
        movie = next((m for m in movies if m["id"] == id), None)

        if movie is None:
            return jsonify({
                "error": "not_found",
                "message": f'Movie with id {id} was not found.'
            }), 404

        movie['title'] = body.get("title")
        movie['director'] = body.get("director")
        movie['year'] = body.get("year")
        movie["watched"] = body.get("watched")

        return jsonify(movie), 200

@app.route('/movies/<int:id>', methods=["DELETE"])
def delete_movie(id):
        """
    Delete a movie by ID

    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID of the movie to delete

    responses:
      204:
        description: Movie successfully deleted

      404:
        description: Movie not found
    """
        global movies
        # find the movies

        movie = next((m for m in movies if m["id"] == id), None)

        if movie is None:
            return jsonify({
                "error": "not_found",
                "message": f"Movie with id {id} was not found."
            }), 404
        # remove it from the list

        movies = [m for m in movies if m["id"] != id]

        # successful delete >> no body, just status

        return "", 204

if __name__ == "__main__":
    app.run(debug=True, port=5000)