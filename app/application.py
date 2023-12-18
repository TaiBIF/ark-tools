import os

from flask import (
    g,
    Flask,
    redirect,
    abort,
)

# from app.database import session
# from app.models import (
#     Ark,
#     Naan,
# )
import sqlite3

def create_app():
    app = Flask(__name__)

    if os.getenv('WEB_ENV') == 'dev':
        app.config.from_object('app.config.DevelopmentConfig')
    elif os.getenv('WEB_ENV') == 'prod':
        app.config.from_object('app.config.ProductionConfig')
    else:
        app.config.from_object('app.config.Config')

    app.url_map.strict_slashes = False
    #print(app.config, flush=True)
    return app

flask_app = create_app()

@flask_app.route('/')
def index():
    return 'pid'

def parse_ark(identifier):
    parts = identifier.split('/')
    if len(parts) < 2:
        raise ValueError('Not a valid ARK')

    naan, assigned_name = parts[:2]
    suffix = identifier[len(naan)+len(assigned_name)+1:]

    try:
        naan_int = int(naan)
    except ValueError:
        raise ValueError('ARK NAAN must be an integer')

    return naan, assigned_name, suffix


@flask_app.route('/ark:/<path:identifier>')
def resolver(identifier):

    suffix = ''
    try:
        naan, assigned_name, suffix = parse_ark(identifier)
    except ValueError as e:
        return abort(400)

    con = sqlite3.connect('ark.db')
    cur = con.cursor()
    res = cur.execute(f"SELECT * FROM ark WHERE identifier = '{naan}/{assigned_name}'")
    if row := res.fetchone():
        if url := row[4]:
            return redirect(f'{url}{suffix}')

    con.close()

    #print(identifier, assigned_name, suffix, naan,flush=True)
    #basic_object_name = f'ark:/{naan}/{assigned_name}'
    #if ark_obj := session.get(Ark, f'{naan}/{assigned_name}'):
    #    print(ark_obj.identifier, ark_obj, flush=True)
    #    print(ark_obj.url, ark_obj.identifier, ark_obj.url, flush=True)
    #    if ark_obj.url:
            #print(ark_obj.url, 'xxx',flush=True)
            #return redirect(f'{ark_obj.url}{suffix}')
    #else:
    #    url = f'https://n2t.net/ark:/{naan}/{assigned_name}'
    #    return redirect(url)

    return abort(404)


#@flask_app.teardown_appcontext
#def shutdown_session(exception=None):
#    # SQLAlchemy won`t close connection, will occupy pool
#    session.remove()

#with flask_app.app_context():
    # needed to make CLI commands work
#    from .commands import *
