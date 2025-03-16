from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'  # Chiave sicura per la sessione

# Funzione per generare un codice stanza casuale
def genera_codice_stanza():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Inizializza il database
def init_db():
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stanze (
                    codice TEXT PRIMARY KEY,
                    chat TEXT,
                    numero_penelope TEXT,
                    numero_eric TEXT,
                    timestamp_countdown INTEGER
                 )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        codice = genera_codice_stanza()
        session.clear()  # Reset della sessione per evitare problemi di identificazione
        session['codice'] = codice

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        c.execute("INSERT INTO stanze (codice, chat, numero_penelope, numero_eric, timestamp_countdown) VALUES (?, ?, ?, ?, ?)",
                  (codice, "", "", "", None))
        conn.commit()
        conn.close()

        print("✅ Creazione stanza:", codice)
        return redirect(url_for('stanza', codice=codice))  # Entra direttamente nella stanza

    return render_template('home.html', codice=None)

@app.route('/ingresso', methods=['POST'])
def ingresso():
    codice_accesso = request.form.get('codice_accesso')

    if not codice_accesso or len(codice_accesso) < 7:
        return "Codice non valido!", 403

    codice_stanza = codice_accesso[2:]

    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT codice FROM stanze WHERE codice = ?", (codice_stanza,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return "Stanza non trovata!", 404

    session.clear()  # Reset ruolo
    if codice_accesso.startswith('59'):
        session['ruolo'] = 'Penelope'
    elif codice_accesso.startswith('33'):
        session['ruolo'] = 'Eric'
    else:
        return "Codice di accesso non valido!", 403

    session['codice'] = codice_stanza
    return redirect(url_for('stanza', codice=codice_stanza))

@app.route('/stanza/<codice>')
def stanza(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat, numero_penelope, numero_eric, timestamp_countdown FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric, timestamp_countdown = stanza
    chat = chat if chat else ""

    return render_template('stanza.html', codice=codice, chat=chat.split("\n"),
                           numero_penelope=numero_penelope if numero_penelope else "Non ancora inserito",
                           numero_eric=numero_eric if numero_eric else "Non ancora inserito",
                           countdown=timestamp_countdown if timestamp_countdown else "Attesa numeri...")

@app.route('/invia_chat/<codice>', methods=['POST'])
def invia_chat(codice):
    ruolo = session.get('ruolo')
    messaggio = request.form.get('messaggio')

    if not ruolo or not messaggio:
        return jsonify({"success": False})

    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
    chat = c.fetchone()[0] if c.fetchone() else ""
    chat += f"\n{ruolo}: {messaggio}"

    c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/aggiorna_chat/<codice>')
def aggiorna_chat(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
    chat = c.fetchone()[0] if c.fetchone() else ""
    conn.close()
    return jsonify({"chat": chat.split("\n")})

@app.route('/invia_numero/<codice>', methods=['POST'])
def invia_numero(codice):
    ruolo = session.get('ruolo')
    numero = request.form.get('numero')

    if not ruolo or not numero:
        return jsonify({"success": False})

    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    
    if ruolo == 'Penelope':
        c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
    elif ruolo == 'Eric':
        c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
    
    c.execute("SELECT numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    
    if stanza and all(stanza):
        timestamp_fine = int(time.time()) + 30  # Countdown di 30 secondi
        c.execute("UPDATE stanze SET timestamp_countdown = ? WHERE codice = ?", (timestamp_fine, codice))

    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/verifica_countdown/<codice>')
def verifica_countdown(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT timestamp_countdown FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza or not stanza[0]:
        return jsonify({"countdown": None})

    tempo_rimanente = max(0, stanza[0] - int(time.time()))
    return jsonify({"countdown": tempo_rimanente})
