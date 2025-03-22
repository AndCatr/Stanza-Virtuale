from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'

# Funzione per generare un codice stanza casuale
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
                    chat_bloccata INTEGER DEFAULT 0,
                    countdown_start INTEGER DEFAULT 0
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
        c.execute("INSERT INTO stanze (codice, chat, numero_penelope, numero_eric, chat_bloccata, countdown_start) VALUES (?, ?, ?, ?, ?, ?)",
                  (codice, "", "", "", 0, 0))
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
    c.execute("SELECT chat, numero_penelope, numero_eric, chat_bloccata FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric, chat_bloccata = stanza

    if request.method == 'POST':
        if 'messaggio' in request.form and not chat_bloccata:
            messaggio = request.form['messaggio']
            chat += f"\n{ruolo}: {messaggio}" if chat else f"{ruolo}: {messaggio}"
            c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))

        if 'numero' in request.form:
            numero = request.form['numero']
            if ruolo == 'Penelope':
                c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
                numero_penelope = numero
            elif ruolo == 'Eric':
                c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
                numero_eric = numero

            # Blocca chat e numeri se entrambi sono presenti e non bloccato
            if numero_penelope and numero_eric and not chat_bloccata:
                timestamp = int(time.time())
                c.execute("UPDATE stanze SET chat_bloccata = 1, countdown_start = ? WHERE codice = ?", (timestamp, codice))

        conn.commit()

    chat_messaggi = [riga.split(": ", 1) for riga in chat.split("\n") if riga.strip()]
    conn.close()

    return render_template('stanza.html', codice=codice, ruolo=ruolo,
                           chat=chat_messaggi,
                           numero_penelope=numero_penelope,
                           numero_eric=numero_eric)

@app.route('/aggiorna_chat/<codice>')
def aggiorna_chat(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    chat = stanza[0].split("\n") if stanza and stanza[0] else []
    chat_messaggi = [riga.split(": ", 1) for riga in chat if ": " in riga]
    return jsonify({"chat": chat_messaggi})

@app.route('/aggiorna_numeri/<codice>')
def aggiorna_numeri(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()
    return jsonify({
        "numero_penelope": stanza[0] if stanza[0] else "Non ancora inserito",
        "numero_eric": stanza[1] if stanza[1] else "Non ancora inserito"
    })

@app.route('/controlla_blocco/<codice>')
def controlla_blocco(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat_bloccata, countdown_start FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return jsonify({"blocco_chat": False, "countdown": -1})

    countdown = -1
    if stanza[1] > 0:
        seconds_elapsed = int(time.time()) - stanza[1]
        countdown = max(0, 30 - seconds_elapsed)

    return jsonify({"blocco_chat": bool(stanza[0]), "countdown": countdown})

if __name__ == '__main__':
    app.run(debug=True)
