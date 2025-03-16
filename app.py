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

# Inizializza il database con un campo per il countdown
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

        return render_template('home.html', codice=codice)

    return render_template('home.html', codice=None)

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

    # Inserimento numeri di telefono
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        if ruolo == 'Penelope':
            c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
        elif ruolo == 'Eric':
            c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
        
        # Controlla se entrambi i numeri sono stati inseriti e avvia il countdown
        c.execute("SELECT numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
        num_pen, num_eric = c.fetchone()

        if num_pen and num_eric and not countdown_start:
            countdown_start = int(time.time())  # Avvia il countdown
            c.execute("UPDATE stanze SET countdown_start = ? WHERE codice = ?", (countdown_start, codice))

        conn.commit()
        conn.close()

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        numero_penelope=numero_penelope or "Non ancora inserito",
        numero_eric=numero_eric or "Non ancora inserito",
        countdown_start=countdown_start
    )

@app.route('/ingresso', methods=['POST'])
def ingresso():
    print("🔹 Tentativo di accesso ricevuto!")  # Log di debug
    codice_accesso = request.form.get('codice_accesso')

    if not codice_accesso or len(codice_accesso) < 7:
        print("❌ Errore: codice non valido")
        return "Codice non valido!", 403

    codice_stanza = codice_accesso[2:]
    print(f"📌 Codice stanza estratto: {codice_stanza}")

    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT codice FROM stanze WHERE codice = ?", (codice_stanza,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        print("❌ Errore: stanza non trovata!")
        return "Stanza non trovata!", 404

    if codice_accesso.startswith('59'):
        session['ruolo'] = 'Penelope'
    elif codice_accesso.startswith('33'):
        session['ruolo'] = 'Eric'
    else:
        print("❌ Errore: codice di accesso non valido!")
        return "Codice di accesso non valido!", 403

    session['codice'] = codice_stanza
    return redirect(url_for('stanza', codice=codice_stanza))

# API per verificare lo stato del countdown
@app.route('/verifica_countdown/<codice>')
def verifica_countdown(codice):
    conn = sqlite3.connect('stanze.db')
    c = conn.cursor()
    c.execute("SELECT countdown_start FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return jsonify({"countdown": False})

    countdown_start = stanza[0]
    return jsonify({"countdown": bool(countdown_start)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
