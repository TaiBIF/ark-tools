import click
import sqlite3
from flask import current_app
from flask.cli import with_appcontext

# NOID character sets
DIGIT_CHARS = '0123456789'
EXTENDED_CHARS = '0123456789bcdfghjkmnpqrstvwxz'  # 29 chars (radix)


def noid_check_digit(s):
    """Calculate NOID check digit using NCDA algorithm."""
    total = 0
    for i, c in enumerate(s, start=1):
        if c in EXTENDED_CHARS:
            total += i * EXTENDED_CHARS.index(c)
    return EXTENDED_CHARS[total % 29]


def validate_noid(assigned_name, template, naan='', shoulder=''):
    """Validate a NOID against its template.

    The check digit is calculated on the full ARK: naan/shoulder+random.

    Returns (is_valid, expected_check, actual_check) for templates with check digit.
    Returns (True, None, None) for templates without check digit.
    """
    # Parse template
    if '.' in template:
        _, mask = template.split('.', 1)
    else:
        mask = template

    if not mask or mask[0] not in 'rsz':
        return (False, None, None)

    pattern = mask[1:]
    has_check = pattern.endswith('k')

    if not has_check:
        return (True, None, None)

    # Validate check digit (calculated on full ARK: naan/shoulder+assigned_name)
    full_ark = f"{naan}/{shoulder}{assigned_name}"
    base = full_ark[:-1]
    actual_check = full_ark[-1]
    expected_check = noid_check_digit(base)

    return (actual_check == expected_check, expected_check, actual_check)


@click.command('noid-check')
@click.option('--ark', '-a', help='Check a specific ARK (e.g., "18474/b2r20t674")')
@click.option('--shoulder', '-s', help='Check all ARKs for a specific shoulder')
@click.option('--limit', '-l', default=0, help='Limit number of ARKs to check (0=all)')
@click.option('--show-invalid', '-i', is_flag=True, help='Only show invalid ARKs')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@with_appcontext
def noid_check(ark, shoulder, limit, show_invalid, verbose):
    """Check NOID validity for ARKs in the database."""

    con = sqlite3.connect('ark.db')
    cur = con.cursor()

    if ark:
        # Check single ARK
        parts = ark.split('/')
        if len(parts) >= 2:
            naan, assigned_name = parts[0], parts[1]
        else:
            click.echo(f"Invalid ARK format: {ark}")
            return

        # Get shoulder (2 or 3 chars)
        res = cur.execute(
            "SELECT shoulder, template FROM shoulder WHERE naan = ? AND (shoulder = ? OR shoulder = ?)",
            (naan, assigned_name[:3], assigned_name[:2])
        )
        row = res.fetchone()
        if not row:
            click.echo(f"Shoulder not found for ARK: {ark}")
            return

        shoulder_name, template = row
        name_without_shoulder = assigned_name[len(shoulder_name):]

        is_valid, expected, actual = validate_noid(name_without_shoulder, template, naan, shoulder_name)

        click.echo(f"ARK:      ark:/{ark}")
        click.echo(f"Shoulder: {shoulder_name}")
        click.echo(f"Template: {template}")
        click.echo(f"Full ID:  {naan}/{shoulder_name}{name_without_shoulder}")
        click.echo(f"Base:     {naan}/{shoulder_name}{name_without_shoulder[:-1] if expected else name_without_shoulder}")
        if expected:
            click.echo(f"Expected: {expected}")
            click.echo(f"Actual:   {actual}")
        click.echo(f"Valid:    {'✓' if is_valid else '✗'}")

    else:
        # Check multiple ARKs
        query = """
            SELECT a.identifier, a.assigned_name, a.shoulder, s.template
            FROM ark a
            JOIN shoulder s ON a.shoulder = s.shoulder
        """
        params = []

        if shoulder:
            query += " WHERE a.shoulder = ?"
            params.append(shoulder)

        if limit > 0:
            query += f" LIMIT {limit}"

        res = cur.execute(query, params)

        total = 0
        valid_count = 0
        invalid_count = 0
        no_check_count = 0
        invalid_arks = []

        for row in res:
            identifier, assigned_name, shoulder_name, template = row
            total += 1

            if not template:
                template = '.reedede'

            # Extract naan from identifier (format: naan/assigned_name)
            naan = identifier.split('/')[0]
            is_valid, expected, actual = validate_noid(assigned_name, template, naan, shoulder_name)

            if expected is None:
                no_check_count += 1
            elif is_valid:
                valid_count += 1
                if verbose and not show_invalid:
                    click.echo(f"✓ ark:/{identifier}")
            else:
                invalid_count += 1
                invalid_arks.append((identifier, expected, actual))
                if verbose or show_invalid:
                    click.echo(f"✗ ark:/{identifier} (expected: {expected}, actual: {actual})")

        click.echo("")
        click.echo("=" * 40)
        click.echo(f"Total checked:    {total}")
        click.echo(f"Valid:            {valid_count}")
        click.echo(f"Invalid:          {invalid_count}")
        click.echo(f"No check digit:   {no_check_count}")

        if invalid_arks and not verbose and not show_invalid:
            click.echo("")
            click.echo(f"First 10 invalid ARKs:")
            for ark_id, expected, actual in invalid_arks[:10]:
                click.echo(f"  ✗ ark:/{ark_id} (expected: {expected}, actual: {actual})")

    con.close()


@click.command('noid-generate')
@click.option('--template', '-t', default='.reedeedk', help='NOID template')
@click.option('--naan', '-n', default='18474', help='NAAN (included in check digit)')
@click.option('--shoulder', '-s', default='b2', help='Shoulder prefix (included in check digit)')
@click.option('--count', '-c', default=1, help='Number of NOIDs to generate')
@with_appcontext
def noid_generate(template, naan, shoulder, count):
    """Generate sample NOIDs using a template."""
    from app.application import generate_noid

    click.echo(f"Template: {template}")
    click.echo(f"NAAN:     {naan}")
    click.echo(f"Shoulder: {shoulder}")
    click.echo(f"Generating {count} NOID(s):")
    click.echo("")

    for _ in range(count):
        noid = generate_noid(template, naan, shoulder)
        full_id = shoulder + noid
        full_ark = f"{naan}/{full_id}"

        # Verify check digit if template has one
        if '.' in template:
            _, mask = template.split('.', 1)
        else:
            mask = template

        has_check = mask[1:].endswith('k') if len(mask) > 1 else False

        if has_check:
            base = full_ark[:-1]
            check = full_ark[-1]
            expected = noid_check_digit(base)
            valid = "✓" if check == expected else "✗"
            click.echo(f"  ark:/{full_ark}  (base: {base}, check: {check}) {valid}")
        else:
            click.echo(f"  ark:/{full_ark}")


def init_app(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(noid_check)
    app.cli.add_command(noid_generate)
