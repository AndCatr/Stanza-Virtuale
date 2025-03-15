from flask import Flask, render_template, request, redirect, url_for, session
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

        print("Creazione stanza:", codice)  # Debug
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

    print("Codice inserito:", codice_accesso)
    print("Codice stanza estratto:", codice_stanza)
    
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
    c.execute("SELECT chat, numero_penelope, numero_eric FROM stanze WHERE codice = ?", (codice,))
    stanza = c.fetchone()
    conn.close()

    if not stanza:
        return "Stanza non trovata!", 404

    chat, numero_penelope, numero_eric = stanza

    # **Gestione chat** (Ora è indentato correttamente)
    if request.method == 'POST' and 'messaggio' in request.form:
        messaggio = request.form['messaggio']
        ruolo = session.get('ruolo', '')

        # Recupera la chat esistente dal database
        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        c.execute("SELECT chat FROM stanze WHERE codice = ?", (codice,))
        result = c.fetchone()
        
        if result:
            chat = result[0] if result[0] else ""  # Se la chat è None, inizializzala come stringa vuota
        else:
            chat = ""

        chat += f"{ruolo}: {messaggio}\n"  # Aggiungi il nuovo messaggio

        # Salva la chat aggiornata nel database
        c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))
        conn.commit()
        conn.close()
        
        print(f"Messaggio ricevuto: {messaggio}")
        print(f"Chat prima dell'aggiornamento: {chat}")
        print(f"Chat dopo l'aggiornamento: {chat}")

    # **Gestione numeri di telefono**
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']

        conn = sqlite3.connect('stanze.db')
        c = conn.cursor()
        if ruolo == 'Penelope':
            c.execute("UPDATE stanze SET numero_penelope = ? WHERE codice = ?", (numero, codice))
        else:
            c.execute("UPDATE stanze SET numero_eric = ? WHERE codice = ?", (numero, codice))
        conn.commit()
        conn.close()

   return render_template(
    'stanza.html',
    codice=codice,
    ruolo=ruolo,
    chat=[riga for riga in chat.split("\n") if riga.strip()],  # Evita righe vuote
    numero_penelope=numero_penelope,
    numero_eric=numero_eric
)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
