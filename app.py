from filecmp import cmp
from flask import Flask, redirect, render_template, request, url_for, session, jsonify
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor
import datetime

app = Flask(__name__)
app.secret_key = "130399"


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hacks'

mysql = MySQL(app)


@app.route('/')
def bienvenue():
    return render_template("bienvenue.html")



@app.route('/conetu')
def conetu():
    return render_template("conetu.html")

@app.route('/conprof')
def conprof():
    return render_template("conprof.html")

@app.route('/conadmin')
def conadmin():
    return render_template("conadmin.html")

from datetime import date, timedelta
from MySQLdb.cursors import DictCursor

@app.route('/connexionetu', methods=['POST'])
def connexionetu():
    email = request.form['email']
    matricule = request.form['matricule']

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM gesteleve WHERE email = %s", (email,))
    etu = cur.fetchone()

    if etu is None:
        cur.close()
        return "Email introuvable"

    
    if etu['matricule'] != matricule:
        cur.close()
        return "Matricule incorrect"

    today = date.today()
    last_login = etu['last_login']
    flame = etu['flame']

    if last_login is None:
        flame = 1
    elif today == last_login:
        pass
    elif today == last_login + timedelta(days=1):
        flame += 1
    else:
        flame = 1

    cur.execute("""
        UPDATE gesteleve
        SET last_login = %s, flame = %s
        WHERE ID = %s
    """, (today, flame, etu['ID']))
    mysql.connection.commit()
    cur.close()

    session['etu_id'] = etu['ID']
    session['etu_nom'] = etu['nom']
    session['etu_prenom'] = etu['prenom']
    session['etu_mat'] = etu['matricule']

    print("Élève connecté :", session)

    return redirect('/dashetu')

@app.route('/inscrietud')
def inscrietud():
    return render_template('insetu.html')
@app.route('/connexionprof', methods=['POST'])
def connexionprof():
    email = request.form['email']
    mdp = request.form['mdp']

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM gestprof WHERE email=%s", (email,))
    prof = cur.fetchone()
    cur.close()

    if not prof or prof['mdp'] != mdp:
        return "Identifiants incorrects"

    session['user_id'] = prof['ID']
    session['prof_nom'] = prof['nom']
    session['prof_prenom'] = prof['prenom']
    return redirect('/filieres')

@app.route('/connexionadmin', methods=['POST'])
def connexionadmin():
    identifiant = request.form['identifiant']
    code = request.form['code']

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM gestadmin WHERE identifiants=%s", (identifiant,))
    admin = cur.fetchone()
    cur.close()

    if not admin or admin['code'] != code:
        return "Identifiants incorrects"

    session['admin_id'] = admin['ID']
    return redirect('/admins')

@app.route('/dashetu')
def dashetu():
    if 'etu_id' not in session:
        return redirect('/conetu')

    today = datetime.date.today()
    etudiant_id = session['etu_id']  

    cur = mysql.connection.cursor(DictCursor)

    cur.execute("SELECT * FROM infos")
    infos = cur.fetchall()
    cur.execute(
        "SELECT nom, flame FROM gesteleve WHERE ID = %s",
        (etudiant_id,)
    )
    use = cur.fetchone()

    cur.execute("""
    SELECT
        COALESCE(SUM(statut = 'present'), 0) AS presences,
        COALESCE(SUM(statut = 'absent'), 0) AS absences
    FROM presenceleve
    WHERE etudiant_id = %s
      AND YEARWEEK(date, 1) = YEARWEEK(CURDATE(), 1)
""", (etudiant_id,))
    result = cur.fetchone()

    niveau = "L1"
    filiere = "INFO"

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT COUNT(*) AS total_etudiants
        FROM gesteleve
        WHERE niveau = %s
        AND filiere = %s
    """, (niveau, filiere))

    total = cur.fetchone()

    etudiant_id = session['etu_id']

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT
            COALESCE(SUM(statut = 'present'), 0) AS presences,
            COALESCE(SUM(statut = 'absent'), 0) AS absences
        FROM presenceleve
        WHERE etudiant_id = %s
        AND YEARWEEK(date, 1) = YEARWEEK(CURDATE(), 1)
    """, (etudiant_id,))
    resulth = cur.fetchone()

    cur.execute("""
        SELECT COUNT(DISTINCT etudiant_id) AS total_presents
        FROM presenceleve
        WHERE statut = 'present'
        AND MONTH(date) = MONTH(CURDATE())
        AND YEAR(date) = YEAR(CURDATE())
    """)
    total_mois = cur.fetchone()

    cur.execute("""
        SELECT COUNT(*) AS total_etudiants
        FROM gesteleve
    """)

    totaux = cur.fetchone()

    cur.close()

    return render_template(
        "dashetu2.html",
        date=today,
        etu_prenom=session.get('etu_prenom'),
        etu_nom=session.get('etu_nom'),
        etu_id=session.get('etu_id'),
        etu_mat=session.get('etu_mat'),
        infos=infos,
        total_mois=total_mois,
        totaux=totaux,
        use=use,
        result=result, 
        total=total,
        resulth=resulth
    )


@app.route('/insetud', methods=['GET', 'POST'])
def insetud():
    if request.method == 'POST':
        data = (
            request.form.get('nom'),
            request.form.get('prenom'),
            request.form.get('matricule'),
            request.form.get('email'),
            request.form.get('niveau'),
            request.form.get('filiere')
        )

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO gesteleve (nom, prenom, matricule, email, niveau, filiere)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, data)
        mysql.connection.commit()
        cur.close()

    return redirect('/dashetu')
@app.route('/inpro')
def inpro():
    return render_template("insprof.html")
@app.route('/insprof', methods=['GET', 'POST'])
def insprof():
    if request.method == 'POST':
        data = (
            request.form.get('nom'),
            request.form.get('prenom'),
            request.form.get('email'),
            request.form.get('pass')
        )

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO gestprof (nom, prenom, email, mdp)
            VALUES (%s, %s, %s, %s)
        """, data)

        mysql.connection.commit()
        cur.close()

        return redirect('/filieres')  
    return render_template('insprof.html')

@app.route('/filieres')
def filieres():
    return render_template(
        "filiereport.html",
        filieres=['INFO','MIAGE','ADA','SECO','SPO'],
        niveaux=['L1','L2','L3','M1','M2']
    )

@app.route('/filtrerprof')
def filtrerprof():
    if 'user_id' not in session:
        return redirect('/conprof')
    
    filiere = request.args.get('filiere')
    niveau = request.args.get('niveau')
    
    if not filiere or not niveau:
        return "Veuillez sélectionner une filière et un niveau", 400
    
    
    return redirect(f'/{filiere}/{niveau}')

@app.route('/<filiere>/<niveau>')
def afficher_etudiants(filiere, niveau):
    if 'user_id' not in session:
        return redirect('/conprof')

    today = datetime.date.today()
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT COUNT(*) AS total_etudiants
        FROM gesteleve WHERE niveau=%s AND filiere=%s
    """, (niveau, filiere))

    totaux = cur.fetchone()
    cur.execute("""
        SELECT COUNT(*) AS pres_etudiants
        FROM presenceleve WHERE statut='present'
    """)

    present = cur.fetchone()
    cur.execute("""
        SELECT COUNT(*) AS abs_etudiants
        FROM presenceleve WHERE statut='absent'
    """)

    absent = cur.fetchone()

    cur.execute("""
        SELECT e.ID, e.nom, e.prenom, e.matricule,
               p.creneau, p.statut
        FROM gesteleve e
        LEFT JOIN presenceleve p
          ON e.ID = p.etudiant_id AND p.date=%s
        WHERE e.filiere=%s AND e.niveau=%s
    """, (today, filiere, niveau))

    rows = cur.fetchall()
    cur.close()

    etudiants = {}
    for r in rows:
        eid = r['ID']
        if eid not in etudiants:
            etudiants[eid] = {
                'ID': eid,
                'nom': r['nom'],
                'prenom': r['prenom'],
                'matricule': r['matricule'],
                'matin1': '',
                'matin2': '',
                'soir1': '',
                'soir2': ''
            }
        if r['creneau']:
            etudiants[eid][r['creneau']] = r['statut']

    return render_template(
        "dashprof2.html",
        totaux=totaux,
        present=present,
        absent=absent,
        gesteleve=etudiants,
        filiere=filiere,
        niveau=niveau,
        date=today
    )


@app.route('/valider_flamme', methods=['POST'])
def valider_flamme():
    etudiant_id = request.form['etudiant_id']
    creneau = request.form['creneau']
    statut = request.form['statut']
    date = datetime.date.today()

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id FROM presenceleve
        WHERE etudiant_id=%s AND date=%s AND creneau=%s
    """, (etudiant_id, date, creneau))

    if cur.fetchone():
        cur.execute("""
            UPDATE presenceleve
            SET statut=%s
            WHERE etudiant_id=%s AND date=%s AND creneau=%s
        """, (statut, etudiant_id, date, creneau))
    else:
        cur.execute("""
            INSERT INTO presenceleve (etudiant_id, date, creneau, statut)
            VALUES (%s,%s,%s,%s)
        """, (etudiant_id, date, creneau, statut))

    mysql.connection.commit()
    cur.close()
    return jsonify(success=True)


@app.route('/admins')
def admins():
    if 'admin_id' not in session:
        return redirect('/conadmin')

    cur = mysql.connection.cursor(DictCursor)
    if 'admin_id' not in session:
        return redirect('/conadmin')
    cur= mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT 
            p.id AS presence_id,
            e.nom AS nom_etudiant,
            e.prenom AS prenom_etudiant,
            e.matricule,
            e.email,
            e.niveau,
            e.filiere,
            e.flame,
            p.statut,
            p.date,
            p.creneau
        FROM presenceleve p
        JOIN gesteleve e ON e.id = p.etudiant_id
        ORDER BY p.date, p.creneau
    """)
    rows = cur.fetchall()


    cur.execute("""
        SELECT
            SUM(statut = 'present') AS total_presents,
            SUM(statut = 'absent') AS total_absents
        FROM presenceleve
        WHERE date = CURDATE()
    """)
    jour = cur.fetchone()


    total = cur.fetchone()

    cur = mysql.connection.cursor(DictCursor)

    cur.execute("""
        SELECT COUNT(*) AS total_etudiants
        FROM gesteleve
    """)

    totaux = cur.fetchone()

    cur.close()

    return render_template(
        "dashadmin2.html",
        pres=rows,
        total=total,
        jour=jour,
        totaux=totaux,
        presences=rows
    )


@app.route('/logoutstud')
def logoutstud():
    session.pop('etu_id')
    return redirect('/conetu', None)
@app.route('/logoutprof')
def logoutprof():
    session.pop('user_id', None)
    return redirect('/conprof')
@app.route('/logoutad')
def logoutad():
    session.pop('ad_id', None)
    return redirect('/conadmin')

if __name__ == "__main__":
    app.run()