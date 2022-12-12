from flask import (
    Blueprint, render_template, redirect, url_for, request, flash,
    session, current_app as app, json, flash
)

from flask_login import login_required, current_user

from discogs_client.exceptions import HTTPError

from ..models import User
from .. import db

discogs_bp = Blueprint(
    'discogs_bp', __name__, url_prefix='/discogs',
    template_folder='templates',
    static_folder='static'
)

@app.errorhandler(HTTPError)
def handle_bad_request(e):
    flash(f"Discogs HTTPError {e.msg}")
    return redirect(url_for('main_bp.profile'))

@discogs_bp.route('login', methods=["GET"])
@login_required
def login():
    print('logging in')
    client = app.get_discogs(current_user)
    _, _, auth_url = client.get_authorize_url(
        url_for('discogs_bp.auth', _external=True)
    )
    return redirect(auth_url)

@discogs_bp.route('auth', methods=["GET"])
@login_required
def auth():
    verifier = request.args.get('oauth_verifier')
    client = app.get_discogs(current_user)
    token, secret = client.get_access_token(verifier)

    current_user.discogs_token = token
    current_user.discogs_secret = secret
    current_user.discogs_account = client.identity().username
    db.session.commit()

    return redirect(url_for('main_bp.profile'))

@discogs_bp.route('logout', methods=["GET"])
@login_required
def logout():
    app.close_discogs(current_user)
    current_user.discogs_token = None
    current_user.discogs_secret = None
    current_user.discogs_account = None
    db.session.commit()

    return redirect(url_for('main_bp.profile'))