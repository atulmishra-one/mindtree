from flask import Flask
from flask import jsonify
from flask import url_for
from flask import request
from flask import make_response
from flask_sqlalchemy import SQLAlchemy
import os
import json
from sqlalchemy.orm.exc import NoResultFound
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = "supersekrit"

blueprint = make_github_blueprint(
    client_id="1246affb4f516fbc48d2",
    client_secret="8a7792c7c094dd848a49589419e2561226ec4cf8",
)

app.register_blueprint(blueprint, url_prefix="/login")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://{}/users.db'.format(os.path.dirname(__file__))
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)

    @staticmethod
    def create():
        user = User(name="Test", username="atulmishra", password="test", email="atul@localhost.com")
        db.session.add(user)
        db.session.commit()


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)


login_manager = LoginManager()
login_manager.login_view = 'github.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)


# create/login local user on successful OAuth login
@oauth_authorized.connect_via(blueprint)
def github_logged_in(blueprint, token):
    if not token:
        return make_response("Failed to log in with GitHub.", 401)

    resp = blueprint.session.get("/user")
    if not resp.ok:
        msg = "Failed to fetch user info from GitHub."
        return make_response(msg, 401)

    github_info = resp.json()
    github_user_id = str(github_info["id"])

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(
        provider=blueprint.name,
        provider_user_id=github_user_id,
    )
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(
            provider=blueprint.name,
            provider_user_id=github_user_id,
            token=token,
        )

    if oauth.user:
        login_user(oauth.user)
        make_response("Successfully signed in with GitHub.", 200)

    else:
        # Create a new local user account for this user
        user = User(
            # Remember that `email` can be None, if the user declines
            # to publish their email address on GitHub!
            email="{}@localhost.com".format(github_info["login"]),
            name=github_info["name"],
            username=github_info['login']
        )
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()
        # Log in the new local user account
        login_user(user)
        return make_response("Successfully signed in with GitHub.", 200)

    # Disable Flask-Dance's default behavior for saving the OAuth token
    return False


# notify on OAuth provider error
@oauth_error.connect_via(blueprint)
def github_error(blueprint, error, error_description=None, error_uri=None):
    msg = (
        "OAuth error from {name}! "
        "error={error} description={description} uri={uri}"
    ).format(
        name=blueprint.name,
        error=error,
        description=error_description,
        uri=error_uri,
    )
    return msg


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(success=True)


# @app.route('/', methods=['POST'])
# def create():
#     code = 201
#     data = request.json
#     try:
#         db.session.add(User(username=data['username'], password=data['password'], email=data['email']))
#         db.session.commit()
#         success = True
#     except Exception as e:
#         print(e)
#         code = 401
#         success = False
#     return make_response(jsonify(status=success), code)


@app.route('/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.filter_by(id=id).one()
    return jsonify(dict(id=user.id, username=user.username, email=user.email, name=user.name))


login_manager.init_app(app)
db.create_all()

if __name__ == '__main__':
    app.run(port="5003")
