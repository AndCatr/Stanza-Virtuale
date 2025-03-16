from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
import sqlite3
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
                    numero_eric TEXT,
                    countdown_start INTEGER
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
        c.execute("INSERT INTO stanze (codice, chat, numero_penelope, numero_eric, countdown_start) VALUES (?, ?, ?, ?, ?)",
                  (codice, "", "", "", None))
        conn.commit()
        conn.close()

        return redirect(url_for('stanza', codice=codice))

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

    # Inserimento chat
    if request.method == 'POST' and 'messaggio' in request.form:
        messaggio = request.form['messaggio']

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        c.execute("UPDATE stanze SET chat = chat || ? WHERE codice = ?", (f"\n{ruolo}: {messaggio}", codice))
        conn.commit()
        conn.close()

    # Inserimento numeri di telefono
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        if ruolo == 'Penelope':
            c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
        elif ruolo == 'Eric':
            c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
        
        # Verifica se entrambi i numeri sono inseriti e avvia il countdown
        c.execute("SELECT numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
        num_pen, num_eric = c.fetchone()

        if num_pen and num_eric and not countdown_start:
            countdown_start = int(time.time())  # Avvio del countdown
            c.execute("UPDATE stanze SET countdown_start = ? WHERE codice = ?", (countdown_start, codice))

        conn.commit()
        conn.close()

    # Chat formattata
    chat_messaggi = [riga.split(": ", 1) for riga in chat.split("\n") if ": " in riga]

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=chat_messaggi,
        numero_penelope=numero_penelope or "Non ancora inserito",
        numero_eric=numero_eric or "Non ancora inserito",
        countdown_start=countdown_start
    )

@app.route('/aggiorna_stato/<codice>')
def aggiorna_stato(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat, numero_penelope, numero_eric, countdown_start FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return jsonify({"errore": "Stanza non trovata!"})

    chat, numero_penelope, numero_eric, countdown_start = stanza
    chat_messaggi = [riga.split(": ", 1) for riga in chat.split("\n") if ": " in riga]

    # Calcolo countdown
    tempo_rimanente = None
    if countdown_start:
        tempo_rimanente = max(0, 30 - (int(time.time()) - countdown_start))

    return jsonify({
        "chat": chat_messaggi,
        "numero_penelope": numero_penelope or "Non ancora inserito",
        "numero_eric": numero_eric or "Non ancora inserito",
        "tempo_rimanente": tempo_rimanente,
        "blocco": bool(tempo_rimanente == 0)
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
