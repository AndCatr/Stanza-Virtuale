from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
import sqlite3
import time  # Per gestire il timestamp

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
                    timestamp_countdown INTEGER
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
        c.execute("INSERT INTO stanze (codice, chat, numero_penelope, numero_eric, timestamp_countdown) VALUES (?, ?, ?, ?, ?)",
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

    print("🔍 Codice inserito:", codice_accesso)
    print("📌 Codice stanza estratto:", codice_stanza)
    
    if not stanza:
        print("❌ Errore: stanza non trovata!")
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
    c.execute("SELECT chat, numero_penelope, numero_eric, timestamp_countdown FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric, timestamp_countdown = stanza

    # Gestione numeri di telefono
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        if ruolo == 'Penelope' and not numero_penelope:
            c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
            numero_penelope = numero  
        elif ruolo == 'Eric' and not numero_eric:
            c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
            numero_eric = numero  
        
        # Avvia il countdown solo dopo che entrambi i numeri sono stati inseriti
        if numero_penelope and numero_eric and not timestamp_countdown:
            timestamp_countdown = int(time.time()) + 30
            c.execute("UPDATE stanze SET timestamp_countdown = ? WHERE codice = ?", (timestamp_countdown, codice))

        conn.commit()
        conn.close()

    # Dividere la chat in coppie (ruolo, messaggio)
    chat_messaggi = [riga.split(": ", 1) for riga in chat.split("\n") if riga.strip()]

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=chat_messaggi,
        numero_penelope=numero_penelope,
        numero_eric=numero_eric
    )

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

@app.route('/verifica_countdown/<codice>')
def verifica_countdown(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT numero_penelope, numero_eric, timestamp_countdown FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return jsonify({"countdown": None})

    numero_penelope, numero_eric, timestamp_countdown = stanza

    if numero_penelope and numero_eric and timestamp_countdown:
        tempo_rimanente = max(0, timestamp_countdown - int(time.time()))  
    else:
        tempo_rimanente = None  

    return jsonify({"countdown": tempo_rimanente})

@app.route('/aggiorna_chat/<codice>')
def aggiorna_chat(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return jsonify({"chat": []})

    chat = stanza[0].split("\n") if stanza[0] else []
    chat_messaggi = [riga.split(": ", 1) for riga in chat if ": " in riga]

    return jsonify({"chat": chat_messaggi})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
