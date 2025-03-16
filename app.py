from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
import sqlite3

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
    c.execute("SELECT chat, numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric = stanza

    # Gestione chat
    if request.method == 'POST' and 'messaggio' in request.form:
        messaggio = request.form['messaggio']
        chat += f"{ruolo}: {messaggio}\n"

        c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))
        conn.commit()

    # Gestione numeri di telefono
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']
        if ruolo == 'Penelope':
            numero_penelope = numero
            c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
        else:
            numero_eric = numero
            c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))

        conn.commit()

        # Controlliamo se entrambi i numeri sono stati inseriti e distruggiamo la stanza
        if numero_penelope and numero_eric:
            c.execute("DELETE FROM stanze WHERE codice = ?", (codice,))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))  # Reindirizza alla home dopo l'autodistruzione

    conn.close()

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=chat.split("\n"),
        numero_penelope=numero_penelope,
        numero_eric=numero_eric
    )

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
