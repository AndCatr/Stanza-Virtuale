from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'

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
                    countdown_avviato INTEGER,
                    countdown_fine TEXT
                 )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        codice = genera_codice_stanza()
        session['codice'] = codice

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        c.execute("INSERT INTO stanze (codice, chat, numero_penelope, numero_eric, countdown_avviato, countdown_fine) VALUES (?, ?, ?, ?, ?, ?)",
                  (codice, "", "", "", 0, None))
        conn.commit()
        conn.close()

        print("✅ Creazione stanza:", codice)
        return render_template('home.html', codice=codice)

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

    if codice_accesso.startswith('59'):
        session['ruolo'] = 'Penelope'
    elif codice_accesso.startswith('33'):
        session['ruolo'] = 'Eric'
    else:
        return "Codice di accesso non valido!", 403

    session['codice'] = codice_stanza
    return redirect(url_for('stanza', codice=codice_stanza))

@app.route('/stanza/<codice>', methods=['GET', 'POST'])
def stanza(codice):
    ruolo = session.get('ruolo')

    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat, numero_penelope, numero_eric, countdown_avviato FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric, countdown_avviato = stanza

    # Gestione chat
    if request.method == 'POST' and 'messaggio' in request.form:
        messaggio = request.form['messaggio']
        ruolo = session.get('ruolo', '')

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
        result = c.fetchone()

        chat = result[0] if result and result[0] else ""
        chat = chat + f"\n{ruolo}: {messaggio}" if chat else f"{ruolo}: {messaggio}"

        c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))
        conn.commit()
        conn.close()

    # Gestione numeri di telefono
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        if ruolo == 'Penelope':
            c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
        elif ruolo == 'Eric':
            c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
        conn.commit()

        # Verifica se entrambi i numeri sono stati inseriti
        c.execute("SELECT numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
        np, ne = c.fetchone()
        if np and ne and not countdown_avviato:
            fine = datetime.datetime.now() + datetime.timedelta(seconds=30)
            c.execute("UPDATE stanze SET countdown_avviato = 1, countdown_fine = ? WHERE codice = ?", (fine.isoformat(), codice))
        conn.commit()
        conn.close()

    chat_messaggi = [riga.split(": ", 1) for riga in chat.split("\n") if riga.strip()]

    return render_template("stanza.html",
                           codice=codice,
                           ruolo=ruolo,
                           chat=chat_messaggi,
                           numero_penelope=numero_penelope,
                           numero_eric=numero_eric)

@app.route('/verifica_countdown/<codice>')
def verifica_countdown(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT countdown_fine FROM stanze WHERE codice = ?", (codice,))
    result = c.fetchone()
    conn.close()

    if not result or not result[0]:
        return jsonify({"countdown": None, "stanza_distrutta": False})

    fine = datetime.datetime.fromisoformat(result[0])
    now = datetime.datetime.now()
    remaining = (fine - now).total_seconds()

    if remaining <= 0:
        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        c.execute("DELETE FROM stanze WHERE codice = ?", (codice,))
        conn.commit()
        conn.close()
        return jsonify({"countdown": 0, "stanza_distrutta": True})

    return jsonify({"countdown": int(remaining), "stanza_distrutta": False})

@app.route('/aggiorna_numeri/<codice>')
def aggiorna_numeri(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return jsonify({"numero_penelope": "", "numero_eric": ""})

    numero_penelope, numero_eric = stanza
    return jsonify({
        "numero_penelope": numero_penelope if numero_penelope else "Non ancora inserito",
        "numero_eric": numero_eric if numero_eric else "Non ancora inserito"
    })

@app.route("/aggiorna_chat/<codice>")
def aggiorna_chat(codice):
    conn = sqlite3.connect("stanze.db")
    c = conn.cursor()
    c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if stanza and stanza[0]:
        chat = stanza[0].split("\n")
        chat_messaggi = [riga.split(": ", 1) for riga in chat if ": " in riga]
    else:
        chat_messaggi = []

    return jsonify({"chat": chat_messaggi})

@app.route('/autodistrutta')
def autodistrutta():
    return """
    <html><head><title>Stanza Distrutta</title></head>
    <body style='background:black; color:red; display:flex; justify-content:center; align-items:center; height:100vh;'>
    <h1>🔥 STANZA DISTRUTTA 🔥</h1>
    </body></html>
    """

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
