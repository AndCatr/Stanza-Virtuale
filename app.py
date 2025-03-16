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
    c.execute("SELECT chat, numero_penelope, numero_eric, countdown_start FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric, countdown_start = stanza

    # Gestione chat
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

    # Gestione numeri di telefono
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
        
        # Se entrambi i numeri sono stati inseriti, avvia il countdown
        c.execute("SELECT numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
        num_pen, num_eric = c.fetchone()

        if num_pen and num_eric and not countdown_start:
            countdown_start = int(time.time())  # Registra l'ora di inizio del countdown
            c.execute("UPDATE stanze SET countdown_start = ? WHERE codice = ?", (countdown_start, codice))

        conn.commit()
        conn.close()

    # Calcolo del tempo rimanente per il countdown
    tempo_rimanente = None
    if countdown_start:
        tempo_rimanente = max(0, 30 - (int(time.time()) - countdown_start))

    # Dividere la chat in coppie (ruolo, messaggio)
    chat_messaggi = [riga.split(": ", 1) for riga in chat.split("\n") if riga.strip()]

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=chat_messaggi,
        numero_penelope=numero_penelope,
        numero_eric=numero_eric,
        tempo_rimanente=tempo_rimanente
    )

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
