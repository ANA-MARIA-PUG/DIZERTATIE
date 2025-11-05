# Importuri necesare
from flask import Flask, jsonify, request
import couchdb
from flask_cors import CORS
from couchdb.design import ViewDefinition

app = Flask(__name__)
# Activam CORS pentru a permite browser-ului (HTML) sa acceseze API-ul
CORS(app)

# --- Configurare Conexiune CouchDB ---
# ATENTIE: Inlocuiti 'ana' si 'anamariapug10' cu credențialele reale.
COUCH_SERVER_URL = 'http://ana:anamariapug10@127.0.0.1:5984/'

# Variabile globale pentru baze de date
DB_PACIENTI = None
DB_DOCTORI = None
DB_ISTORIC = None       # tratament_istoric
DB_PROGRAMARI = None
DB_IMAGINI = None       # imagini_medicale


# Functie pentru initializarea conexiunilor la toate bazele de date
def init_db_connection():
    global DB_PACIENTI, DB_DOCTORI, DB_ISTORIC, DB_PROGRAMARI, DB_IMAGINI

    try:
        couch = couchdb.Server(COUCH_SERVER_URL)

        # Conectare la bazele de date conform structurii din CouchDB
        DB_PACIENTI = couch['pacienti']
        DB_DOCTORI = couch['doctori']
        DB_ISTORIC = couch['tratament_istoric']
        DB_PROGRAMARI = couch['programari']
        DB_IMAGINI = couch['imagini_medicale']

        print("Conexiuni la bazele de date CouchDB stabilite cu succes.")
        return True
    except Exception as e:
        print(f"EROARE CRITICĂ DE CONEXIUNE LA COUCHDB. Verificati URL-ul/Credențialele: {e}")
        return False


# Rulam conexiunea la initializare
if not init_db_connection():
    print("APLICAȚIA FLASK NU POATE PORNI FĂRĂ CONEXIUNEA LA COUCHDB.")


# Functie ajutatoare pentru preluarea tuturor documentelor dintr-o colectie (pentru tabele)
def get_all_docs(db):
    if not db: return []
    # Folosim _all_docs, excludem documentele de design ('_design/')
    # si returnam doar documentul efectiv (.doc)
    return [
        doc.doc
        for doc in db.view('_all_docs', include_docs=True)
        if not doc.id.startswith('_design/')
    ]


# --- Rute API pentru Tabele de Administrare (GET) ---

@app.route('/api/pacienti', methods=['GET'])
def get_pacienti():
    try:
        data = get_all_docs(DB_PACIENTI)
        return jsonify(data)
    except Exception as e:
        return jsonify({"eroare": f"Eroare la preluarea pacienților din CouchDB: {str(e)}"}), 500


@app.route('/api/doctori', methods=['GET'])
def get_doctori():
    try:
        data = get_all_docs(DB_DOCTORI)
        return jsonify(data)
    except Exception as e:
        return jsonify({"eroare": f"Eroare la preluarea doctorilor din CouchDB: {str(e)}"}), 500


@app.route('/api/istoric', methods=['GET'])
def get_istoric():
    try:
        data = get_all_docs(DB_ISTORIC)
        return jsonify(data)
    except Exception as e:
        return jsonify({"eroare": f"Eroare la preluarea istoricului din CouchDB: {str(e)}"}), 500


@app.route('/api/imagini', methods=['GET'])
def get_imagini():
    try:
        data = get_all_docs(DB_IMAGINI)
        return jsonify(data)
    except Exception as e:
        return jsonify({"eroare": f"Eroare la preluarea imaginilor medicale din CouchDB: {str(e)}"}), 500


# --- Ruta API pentru Adaugare Pacient (POST) ---

@app.route('/api/pacienti', methods=['POST'])
def add_pacient():
    if not DB_PACIENTI:
        return jsonify({"eroare": "Conexiunea la baza de date pacienti a eșuat"}), 500

    data = request.json
    if not data or 'nume_complet' not in data:
        return jsonify({"eroare": "Date incomplete. Numele este necesar."}), 400

    # Preluam datele si adaugam un camp de tip
    data['tip_document'] = 'pacient'

    try:
        # Inserarea documentului. CouchDB va genera automat _id și _rev
        doc_id, doc_rev = DB_PACIENTI.save(data)

        # Mesajul de succes este folosit de JavaScript pentru a naviga
        return jsonify({"mesaj": "Pacient adăugat", "id": doc_id}), 201

    except Exception as e:
        return jsonify({"eroare": f"Eroare la inserarea pacientului: {str(e)}"}), 500


# --- Ruta API pentru Analiza Big Data (Venit pe Doctor) ---
@app.route('/api/analiza/venit_doctori', methods=['GET'])
def get_venit_doctori():
    if not DB_ISTORIC:
        return jsonify({"eroare": "Conexiunea la baza de date tratament_istoric a eșuat"}), 500

    try:
        # Interogarea View-ului MapReduce.
        # ATENTIE: Acest View trebuie să existe în baza de date 'tratament_istoric'
        results = DB_ISTORIC.view(
            'analiza_financiara/analiza_financiara',
            group=True
        )

        # Formatarea rezultatelor MapReduce (Key, Value)
        data = []
        for row in results:
            data.append({
                "id_doctor": row.key,
                "venit_total": float(row.value)
            })

        return jsonify(data)
    except Exception as e:
        # Prindem erori daca View-ul nu exista sau nu este indexat
        return jsonify({"eroare": f"Eroare la rularea analizei MapReduce. Verificati calea 'analiza_financiara/analiza_financiara' in DB tratament_istoric: {str(e)}"}), 500


# --- Punct de intrare al aplicatiei ---
if __name__ == '__main__':
    # Flask va rula pe portul 5000, asa cum este asteptat de frontend
    app.run(debug=True, port=5000)