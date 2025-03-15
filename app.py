from flask import Flask, render_template, request, redirect, url_for, session
import random
import string
import sqlite3

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'  # Cambia con una chiave sicura

# Funzione per creare il database se non esiste
def init_db():
    with sqlite3.connect("stanze.db") as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS stanze (
                        codice TEXT PRIMARY KEY,
                        chat TEXT,
                        numero_penelope TEXT,
                        numero_eric TEXT)''')
        conn.commit()

init_db()  # Inizializza il database

# Funzione per generare un codice stanza casuale (alfanumerico di 6 caratteri)
def genera_codice_stanza():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        codice = genera_codice_stanza()
        session['codice'] = codice  # Salva il codice della stanza nella sessione
        
        # Inserisci la nuova stanza nel database
        with sqlite3.connect("stanze.db") as conn:
            c = conn.cursor()
            c.execute("INSERT INTO stanze (codice, chat, numero_penelope, numero_eric) VALUES (?, '', '', '')", (codice,))
            conn.commit()

        return render_template('home.html', codice=codice)

    return render_template('home.html', codice=None)

@app.route('/ingresso', methods=['POST'])
def ingresso():
    codice_accesso = request.form.get('codice_accesso')

    if not codice_accesso or len(codice_accesso) < 7:
        return "Codice non valido!", 403

    codice_stanza = codice_accesso[2:]  # Estrai il codice della stanza

    # Controlla se la stanza esiste nel database
    with sqlite3.connect("stanze.db") as conn:
        c = conn.cursor()
        c.execute("SELECT codice FROM stanze WHERE codice = ?", (codice_stanza,))
        stanza = c.fetchone()

    if not stanza:
        return "Stanza non trovata!", 404

    # Determina il ruolo in base al prefisso
    if codice_accesso.startswith('59'):
        session['ruolo'] = 'Penelope'
    elif codice_accesso.startswith('33'):
        session['ruolo'] = 'Eric'
    else:
        return "Codice di accesso non valido!", 403

    session['codice'] = codice_stanza  # Salva il codice della stanza nella sessione
    return redirect(url_for('stanza', codice=codice_stanza))

@app.route('/stanza/<codice>', methods=['GET', 'POST'])
def stanza(codice):
    ruolo = session.get('ruolo')

    # Controlla se la stanza esiste nel database
    with sqlite3.connect("stanze.db") as conn:
        c = conn.cursor()
        c.execute("SELECT chat, numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
        stanza = c.fetchone()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric = stanza
    chat = chat.split("\n") if chat else []

    # Gestione chat
    if request.method == 'POST' and 'messaggio' in request.form:
        messaggio = request.form['messaggio']
        chat.append(f"{ruolo}: {messaggio}")
        with sqlite3.connect("stanze.db") as conn:
            c = conn.cursor()
            c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", ("\n".join(chat), codice))
            conn.commit()

    # Gestione numeri di telefono
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']
        if ruolo == 'Penelope':
            numero_penelope = numero
            with sqlite3.connect("stanze.db") as conn:
                c = conn.cursor()
                c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero_penelope, codice))
                conn.commit()
        elif ruolo == 'Eric':
            numero_eric = numero
            with sqlite3.connect("stanze.db") as conn:
                c = conn.cursor()
                c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero_eric, codice))
                conn.commit()

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=chat,
        numero_penelope=numero_penelope,
        numero_eric=numero_eric
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
