from flask import Flask, render_template, request, url_for, redirect, flash, url_for
from flask_mysqldb import MySQL
from flask_paginate import Pagination, get_page_parameter
from urllib.parse import urlencode
import openpyxl


app = Flask(__name__)
app.secret_key = "flash"

app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "formation"

mysql = MySQL(app)


########## ADD ############################################

@app.route('/add_from_formation')
def add_from_formation():
    return render_template('add_from_formation.html')

@app.route('/add_from_bailleur')
def add_from_bailleur():
    return render_template('add_from_bailleur.html')

@app.route('/add_from_promo')
def add_from_promo():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bailleur")
    bailleur = cur.fetchall()
    cur.execute("SELECT * FROM formation")
    formation = cur.fetchall()
    cur.close()
    return render_template('add_from_promo.html', formation=formation, bailleur=bailleur)

@app.route('/add_from_simplonien')
def add_from_simplonien():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM promo")
    promo = cur.fetchall()
    cur.close()
    return render_template('add_from_simplonien.html',promo=promo)

@app.route('/add_from_candidat')
def add_from_candidat():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM promo")
    promo = cur.fetchall()
    cur.close()
    return render_template('add_from_candidat.html',promo=promo)



@app.route('/profil/<int:id>', methods=["GET", "POST"])
def profil(id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT candidat.nom, candidat.prenom, candidat.specialite_etude, candidat.lieu_residance, candidat.ville, 
               candidat.email, candidat.telephone, candidat.genre, candidat.nationalite, candidat.date_naissance,
               candidat.statut_sociale, candidat.diplome_actuel, candidat.ecole, promo.nom_promo, formation.nom_formation,
               candidat.contrainte, candidat.source, candidat.decision_finale, candidat.commenter
        FROM promo 
        JOIN candidat ON promo.id = candidat.id_promo 
        JOIN formation ON formation.id = promo.id_formation
        WHERE candidat.id = %s""", (id,))
    profil_info = cur.fetchall()  # Récupère toutes les lignes au lieu d'une seule
    cur.close()
    return render_template('profil.html', profil_info=profil_info)


 
############################################################

@app.route('/candidat', methods=['GET', 'POST'])
def list_candidat():
    # Récupération de la page actuelle depuis l'URL
    page = request.args.get(get_page_parameter(), type=int, default=1)

    # Nombre d'éléments à afficher par page
    per_page = 10

    # Définition des filtres
    id_promo = request.form.get('id_promo')
    id_formation = request.form.get('id_formation')
    promo = get_nom_promo(id_promo) if id_promo else "Choose"
    formation = get_nom_formation(id_formation) if id_formation else "Choose"

    # Construction de la requête SQL en fonction des filtres
    query = "SELECT COUNT(*) FROM promo JOIN candidat ON promo.id = candidat.id_promo JOIN formation ON formation.id = promo.id_formation"
    condition = ""
    params = []

    if id_promo and id_formation:
        condition = " WHERE promo.id = %s AND formation.id = %s"
        query += condition
        params = [id_promo, id_formation]
        promo = get_nom_promo(id_promo)
        formation = get_nom_formation(id_formation)
    elif id_promo:
        condition = " WHERE promo.id = %s"
        query += condition
        params = [id_promo]
        promo = get_nom_promo(id_promo)
        formation = "Choose"
    elif id_formation:
        condition = " WHERE formation.id = %s"
        query += condition
        params = [id_formation]
        promo = "Choose"
        formation = get_nom_formation(id_formation)

    # Récupération du nombre total d'éléments dans la table 'candidat' en fonction des filtres
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    total_count = cur.fetchone()[0]

    # Calcul de l'offset à partir de la page et du nombre d'éléments par page
    offset = (page - 1) * per_page

    # Construction de la requête SQL pour récupérer les éléments à afficher en fonction des filtres
    query = """
        SELECT candidat.id, candidat.nom, candidat.prenom, candidat.telephone, 
               promo.nom_promo, formation.nom_formation, candidat.lieu_residance
        FROM promo 
        JOIN candidat ON promo.id = candidat.id_promo 
        JOIN formation ON formation.id = promo.id_formation
    """
    if condition:
        query += condition
    query += " LIMIT %s OFFSET %s"
    params = params + [per_page, offset]

    # Récupération des éléments à afficher pour la page actuelle en fonction des filtres
    cur.execute(query, params)
    candidat_info = cur.fetchall()

    # Configuration de la pagination avec le nombre total d'éléments et le nombre d'éléments par page
    pagination = Pagination(page=page, total=total_count, per_page=per_page, css_framework='bootstrap5')

    cur.execute("SELECT * FROM promo")
    promo_info = cur.fetchall()

    cur.execute("SELECT * FROM formation")
    formation_info = cur.fetchall()

    cur.close()

    # Rendu du template avec les données récupérées et la pagination
    return render_template('list_candidat.html', promos=promo_info, formations=formation_info, candidat_info=candidat_info, pagination=pagination, promo=promo, formation=formation)


# Correction de la fonction de récupération du nom de promo et de formation
def get_nom_promo(id_promo):
    if id_promo:
        cur = mysql.connection.cursor()
        cur.execute("SELECT nom_promo FROM promo WHERE id = %s", [id_promo])
        nom_promo = cur.fetchone()[0]
        cur.close()
        return nom_promo
    else:
        return ""


def get_nom_formation(id_formation):
    if id_formation:
        cur = mysql.connection.cursor()
        cur.execute("SELECT nom_formation FROM formation WHERE id = %s", [id_formation])
        nom_formation = cur.fetchone()[0]
        cur.close()
        return nom_formation
    else:
        return ""

@app.route('/add_candidat', methods=["POST"])
def add_candidat():
    # Obtenir les données du formulaire
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    telephone = request.form['telephone']
    genre = request.form['genre']
    nationalite = request.form['nationalite']
    date_naissance = request.form['date_naissance']
    lieu_residance = request.form['lieu_residance']
    ville = request.form['ville']
    statut_sociale = request.form['statut_sociale']
    diplome_actuel = request.form['diplome_actuel']
    specialite_etude = request.form['specialite_etude']
    ecole = request.form['ecole']
    id_promo = request.form['id_promo']
    contrainte = request.form['contrainte']
    source = request.form['source']
    decision_finale = request.form['decision_finale']
    
    # Établir une connexion à la base de données
    cur = mysql.connection.cursor()

    # Insérer les données dans la table 'candidat'
    cur.execute("INSERT INTO candidat (nom, prenom, email, telephone, genre, nationalite, date_naissance, lieu_residance, ville, statut_sociale, diplome_actuel, specialite_etude, ecole, id_promo, contrainte, source, decision_finale) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (nom, prenom, email, telephone, genre, nationalite, date_naissance, lieu_residance, ville, statut_sociale, diplome_actuel, specialite_etude, ecole, id_promo, contrainte, source, decision_finale))

    # Valider la transaction
    mysql.connection.commit()

    # Fermer la connexion à la base de données
    cur.close()

    # Rediriger vers la page 'candidat'
    return redirect(url_for('list_candidat'))

@app.route('/import_candidat_excel', methods=['POST'])
def import_candidat_excel():
    if 'fichier_excel' not in request.files:
        flash("Aucun fichier sélectionné")
        return redirect(url_for('listeformation'))
    fichier = request.files['fichier_excel']
    
    # Lecture du fichier Excel
    wb = openpyxl.load_workbook(fichier)
    ws = wb.active

    # Extraction des données
    data = []
    for row in ws.iter_rows(values_only=True):
        data.append(row)

    # Connexion à la base de données
    cur = mysql.connection.cursor()

    # Insertion des données dans la table SQL
    for row in data:
        # Vérification de l'existence de la valeur id_promo dans la table promo
        promo_id = row[14]  # Récupérez la valeur id_promo à partir des données

        # Exécutez une requête SELECT pour vérifier si la valeur existe dans la table promo
        select_query = "SELECT id FROM promo WHERE id = %s"
        cur.execute(select_query, (promo_id,))
        result = cur.fetchone()

        if result:
            # La valeur id_promo existe dans la table promo, vous pouvez insérer les données
            query = "INSERT INTO candidat (nom, prenom, email, telephone, genre, nationalite, date_naissance, lieu_residance, ville, statut_sociale, diplome_actuel, specialite_etude, ecole, id_promo, contrainte, source, decision_finale, commenter) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cur.execute(query, (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18]))
        else:
            # La valeur id_promo n'existe pas dans la table promo, vous pouvez décider de gérer cette situation en conséquence (par exemple, ignorer cette ligne ou afficher un message d'erreur)
            print("La valeur id_promo n'existe pas dans la table promo")

    # Validation et enregistrement des modifications dans la base de données
    mysql.connection.commit()
    cur.close()
    flash("Importation réussie")
    return redirect(url_for('list_candidat'))

############################################################


@app.route('/')
def index():
    return render_template('index.html')

# bailleur
@app.route('/bailleur')
def list_bailleur():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bailleur")
    data = cur.fetchall()
    cur.close()

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10
    offset = (page - 1) * per_page
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM bailleur")
    total_count = cur.fetchone()[0]
    cur.execute("SELECT * FROM bailleur LIMIT %s OFFSET %s", (per_page, offset))
    data = cur.fetchall()
    cur.close()
    pagination = Pagination(page=page, total=total_count, per_page=per_page, css_framework='bootstrap5')
    return render_template('list_bailleur.html', bailleur=data, pagination=pagination)

@app.route('/add_bailleur', methods=["POST"])
def add_bailleur():

    nom_bailleur = request.form['nom_bailleur']
    description = request.form['description']
    # date = request.form['date']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO bailleur (nom_bailleur, description) VALUES (%s,%s)", (nom_bailleur, description))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('list_bailleur'))

@app.route('/upd_bailleur/<int:id>', methods=["GET","POST"])
def upd_bailleur(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bailleur WHERE id=%s", (id,))
    bailleur = cur.fetchone()
    cur.close()

    if request.method == "POST":

        nom_bailleur = request.form['nom_bailleur']
        description = request.form['description']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE bailleur SET nom_bailleur=%s, description=%s WHERE id=%s", (nom_bailleur, description, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_bailleur'))
    
    return render_template('upd_bailleur.html',bailleur=bailleur)
    
@app.route('/delete_bailleur/<string:id_data>', methods=["GET"])
def delete_bailleur(id_data):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM bailleur WHERE id=%s", [id_data])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('list_bailleur'))

#############################################################################################

# formation
@app.route('/formation')
def list_formation():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM formation")
    data = cur.fetchall()
    cur.close()

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10
    offset = (page - 1) * per_page
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM formation")
    total_count = cur.fetchone()[0]
    cur.execute("SELECT * FROM formation LIMIT %s OFFSET %s", (per_page, offset))
    data = cur.fetchall()
    cur.close()
    pagination = Pagination(page=page, total=total_count, per_page=per_page, css_framework='bootstrap5')
    return render_template('list_formation.html', formation=data, pagination=pagination)

@app.route('/add_formation', methods=["POST"])
def add_formation():

    nom_formation = request.form['nom_formation']
    duree = request.form['duree']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO formation (nom_formation, duree) VALUES (%s,%s)", (nom_formation, duree))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('list_formation'))

@app.route('/upd_formation/<int:id>', methods=["GET","POST"])
def upd_formation(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM formation WHERE id=%s", (id,))
    formation = cur.fetchone()
    cur.close()

    if request.method == "POST":

        nom_formation = request.form['nom_formation']
        duree = request.form['duree']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE formation SET nom_formation=%s, duree=%s WHERE id=%s", (nom_formation, duree, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_formation'))
    
    return render_template('upd_formation.html',formation=formation)
    
@app.route('/delete_formation/<string:id_data>', methods=["GET"])
def delete_formation(id_data):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM formation WHERE id=%s", [id_data])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('list_formation'))

######################################################################################################################

# promo
@app.route('/promo')
def list_promo():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            promo.id, promo.nom_promo, bailleur.nom_bailleur, 
            formation.nom_formation, promo.debut_promo, 
            promo.fin_promo 
        FROM 
            bailleur 
        JOIN 
            promo ON bailleur.id = promo.id_bailleur 
        JOIN 
            formation ON formation.id = promo.id_formation
    """)
    data = cur.fetchall()
    cur.close()
    return render_template('list_promo.html',promo=data)

@app.route('/add_promo', methods=["POST"])
def add_promo():

    # Obtenir les données du formulaire
    nom_promo = request.form['nom_promo']
    id_bailleur = request.form['id_bailleur']
    id_formation = request.form['id_formation']
    debut_promo = request.form['debut_promo']
    fin_promo = request.form['fin_promo']

    # Établir une connexion à la base de données
    cur = mysql.connection.cursor()

    # Insérer les données dans la table 'promo'
    cur.execute("INSERT INTO promo (nom_promo, id_bailleur, id_formation, debut_promo, fin_promo) VALUES (%s, %s, %s, %s, %s)", (nom_promo, id_bailleur, id_formation, debut_promo, fin_promo))

    # Valider la transaction
    mysql.connection.commit()

    # Fermer la connexion à la base de données
    cur.close()

    # Rediriger vers la page 'promo'
    return redirect(url_for('list_promo'))

@app.route('/upd_promo/<int:id>', methods=["GET","POST"])
def upd_promo(id):

    cur = mysql.connection.cursor()
    cur.execute("SELECT promo.id, promo.nom_promo, bailleur.nom_bailleur, formation.nom_formation, promo.debut_promo, promo.fin_promo FROM bailleur JOIN promo ON bailleur.id = promo.id_bailleur JOIN formation ON formation.id = promo.id_formation WHERE promo.id=%s",(id,))
    promo_info = cur.fetchall()
    cur.execute("SELECT * FROM bailleur")
    bailleur = cur.fetchall()
    cur.execute("SELECT * FROM formation")
    formation = cur.fetchall()
    cur.close()

    if request.method == "POST":

        nom_promo = request.form['nom_promo']
        id_bailleur = request.form['id_bailleur']
        id_formation = request.form['id_formation']
        debut_promo = request.form['debut_promo']
        fin_promo = request.form['fin_promo']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE promo SET nom_promo=%s, id_bailleur=%s, id_formation=%s, debut_promo=%s, fin_promo=%s WHERE id=%s", (nom_promo, id_bailleur, id_formation, debut_promo, fin_promo, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_promo'))
    
    return render_template('upd_promo.html',promo_info=promo_info, bailleur=bailleur,formation=formation)

@app.route('/delete_promo/<string:id_data>', methods=["GET"])
def delete_promo(id_data):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM promo WHERE id=%s", [id_data])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('list_promo'))

####################################################################################################################

#simplonien
@app.route('/simplonien')
def list_simplonien():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            simplonien.id, simplonien.nom, simplonien.prenom, 
            simplonien.telephone, promo.nom_promo, formation.nom_formation, 
            simplonien.tuteur, simplonien.residance 
        FROM 
            promo 
        JOIN 
            simplonien ON promo.id = simplonien.id_promo 
        JOIN 
            formation ON formation.id = promo.id_formation
    """)
    data = cur.fetchall()
    cur.close()
    return render_template('list_simplonien.html', simplonien=data)

@app.route('/add_simplonien', methods=["POST"])
def add_simplonien():

    # Obtenir les données du formulaire
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    telephone = request.form['telephone']
    id_promo = request.form['id_promo']
    tuteur = request.form['tuteur']
    residance = request.form['residance']
    # Établir une connexion à la base de données
    cur = mysql.connection.cursor()

    # Insérer les données dans la table 'simplonien'
    cur.execute("INSERT INTO simplonien (nom, prenom, email, telephone, id_promo, tuteur, residance) VALUES (%s, %s, %s, %s, %s, %s, %s)", (nom, prenom, email, telephone, id_promo, tuteur, residance))

    # Valider la transaction
    mysql.connection.commit()

    # Fermer la connexion à la base de données
    cur.close()

    # Rediriger vers la page 'simplonien'
    return redirect(url_for('list_simplonien'))

@app.route('/upd_simplonien/<int:id>', methods=["GET","POST"])
def upd_simplonien(id):

    cur = mysql.connection.cursor()
    # cur.execute("SELECT promo.id, promo.nom_promo, bailleur.nom_bailleur, formation.nom_formation, promo.debut_promo, promo.fin_promo FROM bailleur JOIN promo ON bailleur.id = promo.id_bailleur JOIN formation ON formation.id = promo.id_formation WHERE promo.id=%s", (id,))
    cur.execute("""
        SELECT 
            simplonien.id, simplonien.nom, simplonien.prenom, simplonien.email, 
            simplonien.telephone, promo.nom_promo, simplonien.tuteur, simplonien.residance 
        FROM 
            promo 
        JOIN 
            simplonien ON promo.id = simplonien.id_promo
        WHERE 
            simplonien.id=%s
    """, (id,))
    simplonien_info = cur.fetchall()
    cur.close()

    if request.method == "POST":

    # Obtenir les données du formulaire
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form['telephone']
        tuteur = request.form['tuteur']
        residance = request.form['residance']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE simplonien SET nom=%s, prenom=%s, email=%s, telephone=%s, tuteur=%s, residance=%s WHERE id=%s", (nom, prenom, email, telephone, tuteur, residance, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_simplonien'))
    
    return render_template('upd_simplonien.html',simplonien_info=simplonien_info)

@app.route('/delete_simplonien/<string:id_data>', methods=["GET"])
def delete_simplonien(id_data):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM simplonien WHERE id=%s", [id_data])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('list_simplonien'))

if __name__ == "__main__":
    app.run(debug=True)