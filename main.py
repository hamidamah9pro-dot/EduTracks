from warnings import filters
from flask import Flask, redirect, render_template, request, url_for, session
from flask_mysqldb import MySQL
import datetime
from MySQLdb.cursors import DictCursor
from flask import Flask, jsonify, session
from datetime import date, timedelta
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "130399"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hack'
mysql = MySQL(app)



@app.route('/')
def bienvenue():
    return render_template("bienvenue.html")
@app.route('/connexionetu', methods=['POST'])
def connexionetu():
    email = request.form['email']
    matricule = request.form['matricule']
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM gesteleve WHERE email = %s", (email,))
    etu = cur.fetchone()
    if etu and check_password_hash(etu['matricule'], matricule):
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

        cur.execute("""UPDATE gesteleve SET last_login = %s, flame =  %s""", (today, flame, etu['ID']))
        mysql.connection.commit()
        cur.close()    
    
    if etu is None:
        return "Email Introuvable"
    if etu['matricule'] != matricule:
        return "Mot de Passe incorect"
    
    session['etu_id'] = etu['ID']
    session['etu_nom'] = etu['nom']
    session['etu_prenom'] = etu['prenom']
    if "etu_id" in session:
       print("L'utilisateur est connecté")
    print ("SESSION PROF :", session)
    return redirect('/dashetu')
@app.route('/connexionprof', methods=['POST'])
def connexionprof():
    email = request.form['email']
    mdp = request.form['mdp']
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM gestprof WHERE email = %s", (email,))
    user = cur.fetchone()

        
    if user is None:
        return "Email Introuvable"
    if user['mdp'] != mdp:
        return "Mot de Passe incorect"
    
    session['user_id'] = user['ID']
    session['prof_nom'] = user['nom']
    session['prof_prenom'] = user['prenom']
    if "user_id" in session:
       print("L'utilisateur est connecté")
    print ("SESSION PROF :", session)
    return redirect('/filieres')
@app.route('/connexionadmin', methods=['POST'])
def connexionadmin():
    identifiant = request.form['identifiant']
    code = request.form['code']
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM gestadmin WHERE identifiants = %s", (identifiant,))
    admin = cur.fetchone()

        
    if admin is None:
        return "ID Introuvable"
    if admin['code'] != code:
        return "CODE incorect"
    
    session['admin_id'] = admin['ID']
    session['ad_idd'] = admin['identifiants']
    session['ad_code'] = admin['code']
    if "user_id" in session:
       print("L'utilisateur est connecté")
    print ("SESSION PROF :", session)
    return redirect('/admins')
@app.route('/conetu')
def conetu():
    return render_template("conetu.html")
@app.route('/conprof')
def conprof():
    return render_template("conprof.html")
@app.route('/conadmin')
def conadmin():
    return render_template("conadmin.html")
@app.route('/dashetu')
def dashetu():
    date = datetime.date.today()
    etu_prenom = session.get('etu_prenom')
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""SELECT nom, flame FROM gesteleve WHERE ID = %s """, (session['etu_id'],))
    use = cur.fetchone()
    cur.close()
    return render_template("dashetu.html", date=date, etu_prenom=etu_prenom, use=use)
@app.route('/insetud', methods=['GET', 'POST'])
def insetud():
   if request.method == 'POST':

        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        matricule = request.form.get('matricule')
        email = request.form.get('email')
        niveau = request.form.get('niveau')
        filiere = request.form.get('filiere')

        cur = mysql.connection.cursor()
        cur.execute(" INSERT INTO gesteleve (nom, prenom, matricule, email, niveau, filiere) VALUES (%s, %s, %s, %s, %s, %s)", (nom, prenom, matricule, email, niveau, filiere))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashetu'))
@app.route("/filieres", methods=["GET"])
def filieres():
    filiere = request.args.get("filiere")
    niveau = request.args.get("niveau")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM gesteleve WHERE filiere=%s AND niveau=%s", (filiere, niveau))
    data = cur.fetchall()
    cur.close()

    filieres = {
        'INFO': 'INFO',
        'MIAGE': 'MIAGE',
        'ADA': 'ADA',
        'SECO': 'SECO',
        'SPO': 'SPO'
    }

    niveaux = ["L1", "L2", "L3", "M1", "M2"]

    return render_template("filiereport.html", gesteleve=data, filieres=filieres, niveaux=niveaux)
@app.route('/insprof', methods=['GET', 'POST'])
def insprof():
     if request.method == 'POST':

        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        mdp = request.form.get('pass')

        cure = mysql.connection.cursor()
        cure.execute("""
            INSERT INTO gestprof (nom, prenom, email, mdp)
            VALUES (%s, %s, %s, %s)
        """, (nom, prenom, email, mdp))

        mysql.connection.commit()
        cure.close()
        
        return redirect(url_for("filiere"))
@app.route('/<filiere>/<niveau>')
def afficher_etudiants(filiere, niveau):
    from datetime import date
    cur = mysql.connection.cursor(DictCursor)
    tdy = date.today()

    cur.execute("""
        SELECT e.ID, e.nom, e.prenom, e.matricule,
               p.date, p.creneau, p.statut
        FROM gesteleve e
        LEFT JOIN presenceleve p ON e.ID = p.etudiant_id
        WHERE e.niveau=%s AND e.filiere=%s
    """, (niveau, filiere))
    etudiants = cur.fetchall()

    etudiants = {}
    for row in etudiants:
        eid = row['ID']
        if eid not in etudiants:
            etudiants[eid] = {
                'ID': eid,
                'nom': row['nom'],
                'prenom': row['prenom'],
                'matricule': row['matricule'],
                'matin1': '',
                'matin2': '',
                'soir1': '',
                'soir2': ''
            }
        if row['creneau']:
            etudiants[eid][row['creneau']] = row['statut']

    cur.execute("SELECT nom, prenom FROM gestprof")
    profs = cur.fetchall()

    cur.close()
    return render_template("allstud.html", gesteleve=etudiants, gestprof=profs, jj=tdy, filiere=filiere, niveau=niveau)

@app.route('/filtrerprof')
def filtrerprof():
    if 'user_id' not in session:
        return redirect('/conprof')
    filiere = request.args.get('filiere')
    niveau = request.args.get('niveau')
    date = datetime.date.today()
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT e.ID, e.nom, e.prenom, e.matricule,
        FROM gesteleve e
        LEFT JOIN presenceleve p ON e.ID = p.etudiant_id
        WHERE e.niveau=%s AND e.filiere=%s
    """, (niveau, filiere))
    etudiants = cur.fetchall()
    cur.close()
    prof_nom = session.get('prof_nom')
    prof_prenom = session.get('prof_prenom')
    
    return render_template("allstud.html", filiere=filiere, niveau=niveau, etudiants=etudiants, prof_nom=prof_nom, prof_prenom=prof_prenom, date=date)
@app.route('/admins')
def admins():
    if 'admin_id' not in session:
        return redirect('/conadmin')
    cur= mysql.connection.cursor(DictCursor)
    prof_id = 1  # exemple
    cur.execute("""
    SELECT 
        p.id AS presence_id,
        e.nom AS nom_etudiant,
        e.prenom AS prenom_etudiant,
        pr.nom AS nom_prof,
        pr.prenom AS prenom_prof,
        p.date,
        p.creneau,
        p.statut
    FROM presenceleve p
    JOIN gesteleve e ON e.id = p.etudiantid
    JOIN gestprof pr ON pr.ID = p.prof_id
    WHERE pr.ID = %s
    ORDER BY p.date, p.creneau
    """, (prof_id,))
    rows = cur.fetchall()
    cur.close()
    return render_template("dashadmin.html", pres=rows)

@app.route('/valider_flamme', methods=['POST'])
def valider_flamme():
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT `ID`, `etudiant_id`, `streak` FROM `flammes` WHERE 1")
    return
if __name__ == "__main__":
    app.run(debug=True)