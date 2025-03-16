from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
import sqlite3
import threading
import time

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'  # Cambia con una chiave sicura

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
                    numero_eric TEXT
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
        c.execute("INSERT INTO stanze (codice, chat, numero_penelope, numero_eric) VALUES (?, ?, ?, ?)",
                  (codice, "", "", ""))
        conn.commit()
        conn.close()

        return redirect(url_for('stanza', codice=codice))

    return render_template('home.html')

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
    c.execute("SELECT chat, numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric = stanza

    chat_bloccata = bool(numero_penelope and numero_eric)

    if request.method == 'POST':
        if 'messaggio' in request.form and not chat_bloccata:
            messaggio = request.form['messaggio']
            chat += f"{ruolo}: {messaggio}\n"

            conn = sqlite3.connect('stanze.db')
            c = conn.cursor()
            c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))
            conn.commit()
            conn.close()

        elif 'numero' in request.form:
            numero = request.form['numero']

            conn = sqlite3.connect('stanze.db')
            c = conn.cursor()
            if ruolo == 'Penelope':
                c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
            else:
                c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
            conn.commit()
            conn.close()

            if numero_penelope and numero_eric:
                threading.Thread(target=elimina_stanza, args=(codice,)).start()

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=chat.split("\n"),
        numero_penelope=numero_penelope,
        numero_eric=numero_eric,
        chat_bloccata=chat_bloccata
    )

@app.route('/aggiorna_chat/<codice>')
def aggiorna_chat(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat, numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return jsonify({"chat": [], "chat_bloccata": True})

    chat, numero_penelope, numero_eric = stanza
    chat_messaggi = [riga.split(": ", 1) for riga in chat.split("\n") if ": " in riga]
    chat_bloccata = bool(numero_penelope and numero_eric)

    return jsonify({"chat": chat_messaggi, "chat_bloccata": chat_bloccata})

def elimina_stanza(codice):
    time.sleep(30)
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("DELETE FROM stanze WHERE codice = ?", (codice,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
