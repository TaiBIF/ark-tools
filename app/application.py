import os

import secrets
import functools

from flask import (
    g,
    Flask,
    redirect,
    abort,
    request,
    jsonify,
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

# Register CLI commands
from app import commands
commands.init_app(flask_app)

@flask_app.route('/')
def index():
    return 'pid'


def require_api_key(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != flask_app.config.get('MINTER_API_KEY'):
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated


# NOID character sets
DIGIT_CHARS = '0123456789'
EXTENDED_CHARS = '0123456789bcdfghjkmnpqrstvwxz'  # 29 chars (radix)


def noid_check_digit(s):
    """Calculate NOID check digit using NCDA algorithm."""
    total = 0
    for i, c in enumerate(s, start=1):
        if c in EXTENDED_CHARS:
            ordinal = EXTENDED_CHARS.index(c)
        else:
            ordinal = 0
        total += i * ordinal
    return EXTENDED_CHARS[total % len(EXTENDED_CHARS)]


def parse_noid_template(template):
    """Parse NOID template into prefix and mask.

    Template format: prefix.mask
    Mask starts with generator type (r=random, s=sequential, z=unlimited)
    followed by: d (digit), e (extended digit), k (check digit at end)

    Example: .reeeeee -> prefix='', generator='r', mask='eeeeee'
    """
    if '.' in template:
        prefix, mask = template.split('.', 1)
    else:
        prefix, mask = '', template

    if not mask:
        raise ValueError('Template mask is required')

    generator = mask[0]
    if generator not in 'rsz':
        raise ValueError(f'Invalid generator type: {generator}')

    pattern = mask[1:]
    has_check = pattern.endswith('k')
    if has_check:
        pattern = pattern[:-1]

    for c in pattern:
        if c not in 'de':
            raise ValueError(f'Invalid mask character: {c}')

    return {
        'prefix': prefix,
        'generator': generator,
        'pattern': pattern,
        'has_check': has_check,
    }


def generate_noid(template, naan='', shoulder=''):
    """Generate a NOID identifier based on template.

    The check digit (if template has 'k') is calculated on full ARK: naan/shoulder+random.
    Returns only the random part (without shoulder).
    """
    parsed = parse_noid_template(template)

    result = parsed['prefix']

    for c in parsed['pattern']:
        if c == 'd':
            result += secrets.choice(DIGIT_CHARS)
        elif c == 'e':
            result += secrets.choice(EXTENDED_CHARS)

    if parsed['has_check']:
        # Check digit calculated on full ARK including naan/shoulder
        full_ark = f"{naan}/{shoulder}{result}"
        result += noid_check_digit(full_ark)

    return result


@flask_app.route('/api/mint', methods=['POST'])
@require_api_key
def mint():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    naan = data.get('naan')
    shoulder = data.get('shoulder')
    url = data.get('url')

    if not all([naan, shoulder, url]):
        return jsonify({'error': 'naan, shoulder, and url are required'}), 400

    try:
        naan = int(naan)
    except ValueError:
        return jsonify({'error': 'naan must be an integer'}), 400

    who = data.get('who', '')
    what = data.get('what', '')
    when = data.get('when', '')

    con = sqlite3.connect('ark.db')
    cur = con.cursor()

    # verify naan exists
    res = cur.execute('SELECT * FROM naan WHERE naan = ?', (naan,))
    if not res.fetchone():
        con.close()
        return jsonify({'error': f'NAAN {naan} not found'}), 404

    # verify shoulder exists and get template
    res = cur.execute('SELECT shoulder, naan, name, description, redirect_prefix, template FROM shoulder WHERE shoulder = ? AND naan = ?', (shoulder, naan))
    shoulder_row = res.fetchone()
    if not shoulder_row:
        con.close()
        return jsonify({'error': f'Shoulder {shoulder} not found for NAAN {naan}'}), 404

    # priority: request template > shoulder template > default
    shoulder_template = shoulder_row[5] if shoulder_row[5] else '.reedede'
    template = data.get('template', shoulder_template)

    try:
        parsed = parse_noid_template(template)
    except ValueError as e:
        con.close()
        return jsonify({'error': f'Invalid template: {e}'}), 400

    # generate unique assigned_name
    for _ in range(10):
        random_part = generate_noid(template, naan, shoulder)
        assigned_name = f'{shoulder}{random_part}'
        identifier = f'{naan}/{assigned_name}'

        res = cur.execute('SELECT * FROM ark WHERE identifier = ?', (identifier,))
        if not res.fetchone():
            break
    else:
        con.close()
        return jsonify({'error': 'Failed to generate unique identifier'}), 500

    # insert new ARK
    cur.execute(
        'INSERT INTO ark (identifier, naan, assigned_name, shoulder, url, who, what, "when") VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (identifier, naan, assigned_name, shoulder, url, who, what, when)
    )
    con.commit()
    con.close()

    return jsonify({
        'ark': f'ark:/{identifier}',
        'identifier': identifier,
        'url': url,
    }), 201


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

    #print(identifier, naan, assigned_name, suffix, flush=True)

    con = sqlite3.connect('ark.db')
    cur = con.cursor()
    res = cur.execute(f"SELECT * FROM ark WHERE identifier = '{naan}/{assigned_name}'")
    if row := res.fetchone():
        if url := row[4]:
            return redirect(f'{url}{suffix}')

    # not match object, try shoulder, redirect
    # shoulder can be 2 or 3 char
    shoulder2 = assigned_name[:2]
    shoulder3 = assigned_name[:3]
    res = cur.execute(f"SELECT * FROM shoulder WHERE naan = '{naan}' AND (shoulder = '{shoulder3}' OR shoulder = '{shoulder2}')")
    if row := res.fetchone():
        if url := row[4]:
            target_name = assigned_name[len(row[0]):]
            return redirect(f'{url}{target_name}')

    con.close()

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
