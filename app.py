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
                    chat TEXT DEFAULT '',
                    numero_penelope TEXT DEFAULT '',
                    numero_eric TEXT DEFAULT '',
                    countdown_start INTEGER DEFAULT NULL
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
        c.execute("INSERT INTO stanze (codice) VALUES (?)", (codice,))
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
    c.execute("SELECT chat, numero_penelope, numero_eric, countdown_start FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric, countdown_start = stanza

    # Avvio del countdown
    if countdown_start:
        tempo_rimanente = max(0, 30 - (int(time.time()) - countdown_start))
    else:
        tempo_rimanente = None

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=[riga.split(": ", 1) for riga in chat.split("\n") if riga.strip()],
        numero_penelope=numero_penelope,
        numero_eric=numero_eric,
        tempo_rimanente=tempo_rimanente
    )

# API per aggiornare la chat
@app.route('/aggiorna_chat/<codice>')
def aggiorna_chat(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return jsonify({"chat": []})

    chat = stanza[0].split("\n")
    chat_messaggi = [riga.split(": ", 1) for riga in chat if ": " in riga]

    return jsonify({"chat": chat_messaggi})

# API per aggiornare i numeri di telefono
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

# API per controllare il countdown e bloccare la chat
@app.route('/verifica_countdown/<codice>')
def verifica_countdown(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT countdown_start FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza or not stanza[0]:
        return jsonify({"countdown": None})

    tempo_rimanente = max(0, 30 - (int(time.time()) - stanza[0]))
    return jsonify({"countdown": tempo_rimanente})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
