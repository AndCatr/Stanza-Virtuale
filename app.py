from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'

def genera_codice_stanza():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def init_db():
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stanze (
                    codice TEXT PRIMARY KEY,
                    chat TEXT,
                    numero_penelope TEXT,
                    numero_eric TEXT,
                    countdown_avviato INTEGER
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
        c.execute("INSERT INTO stanze (codice, chat, numero_penelope, numero_eric, countdown_avviato) VALUES (?, ?, ?, ?, ?)",
                  (codice, "", "", "", None))
        conn.commit()
        conn.close()
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

    if request.method == 'POST' and 'messaggio' in request.form:
        messaggio = request.form['messaggio']
        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
        result = c.fetchone()
        chat = result[0] if result and result[0] else ""
        chat = chat + f"\n{ruolo}: {messaggio}" if chat else f"{ruolo}: {messaggio}"
        c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))
        conn.commit()
        conn.close()

    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']
        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        if ruolo == 'Penelope':
            c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
            numero_penelope = numero
        elif ruolo == 'Eric':
            c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
            numero_eric = numero

        if numero_penelope and numero_eric and not countdown_avviato:
            timestamp = int(time.time()) + 30
            c.execute("UPDATE stanze SET countdown_avviato = ? WHERE codice = ?", (timestamp, codice))

        conn.commit()
        conn.close()

    chat_messaggi = [riga.split(": ", 1) for riga in chat.split("\n") if riga.strip()]
    return render_template('stanza.html', codice=codice, ruolo=ruolo,
                           chat=chat_messaggi, numero_penelope=numero_penelope,
                           numero_eric=numero_eric)

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

@app.route('/controlla_blocco/<codice>')
def controlla_blocco(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()
    if not stanza:
        return jsonify({"blocco_numero_penelope": False, "blocco_numero_eric": False, "blocco_chat": False})
    numero_penelope, numero_eric = stanza
    blocco_numero_penelope = bool(numero_penelope)
    blocco_numero_eric = bool(numero_eric)
    blocco_chat = blocco_numero_penelope and blocco_numero_eric
    return jsonify({
        "blocco_numero_penelope": blocco_numero_penelope,
        "blocco_numero_eric": blocco_numero_eric,
        "blocco_chat": blocco_chat
    })

@app.route('/verifica_countdown/<codice>')
def verifica_countdown(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT countdown_avviato FROM stanze WHERE codice = ?", (codice,))
    result = c.fetchone()
    if not result:
        conn.close()
        return jsonify({"countdown": None})
    timestamp = result[0]
    if timestamp and time.time() >= timestamp:
        c.execute("DELETE FROM stanze WHERE codice = ?", (codice,))
        conn.commit()
        conn.close()
        return jsonify({"countdown": 0})
    tempo_rimanente = max(0, timestamp - int(time.time())) if timestamp else None
    conn.close()
    return jsonify({"countdown": tempo_rimanente})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
