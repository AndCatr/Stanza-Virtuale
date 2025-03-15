from flask import Flask, render_template, request, redirect, url_for, session
import random
import string

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'chiave_super_segreta'

# Simuliamo un database con un dizionario
stanze = {}

# Funzione per generare un codice stanza casuale
def genera_codice_stanza():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        codice = genera_codice_stanza()
        session['codice'] = codice  # Salva il codice della stanza nella sessione
        
        # 🔹 Assicuriamoci di salvare la stanza correttamente
        print("Creazione stanza:", codice)  # Debug
        stanze[codice] = {"chat": [], "numeri": {"Penelope": "", "Eric": ""}}
        print("Stanze attuali:", stanze.keys())  # Debug
        
        # Crea la stanza
        stanze[codice] = {"chat": [], "numeri": {"Penelope": "", "Eric": ""}}

        return render_template('home.html', codice=codice)

    return render_template('home.html', codice=None)

@app.route('/ingresso', methods=['POST'])
def ingresso():
    codice_accesso = request.form.get('codice_accesso')

    # Controllo che il codice sia abbastanza lungo
    if not codice_accesso or len(codice_accesso) < 7:
        return "Codice non valido!", 403

    # Estrai il codice della stanza rimuovendo i primi due caratteri
    codice_stanza = codice_accesso[2:]

  # 🔹 STAMPE DI DEBUG 🔹
    print("Codice inserito:", codice_accesso)
    print("Codice stanza estratto:", codice_stanza)
    print("Stanze disponibili:", stanze.keys())

    # Verifica se la stanza esiste
    if codice_stanza not in stanze:
        return "Stanza non trovata!", 404

    # Determina il ruolo in base al prefisso
    if codice_accesso.startswith('59'):
        session['ruolo'] = 'Penelope'
    elif codice_accesso.startswith('33'):
        session['ruolo'] = 'Eric'
    else:
        return "Codice di accesso non valido!", 403

    # Salva il codice della stanza nella sessione
    session['codice'] = codice_stanza
    return redirect(url_for('stanza', codice=codice_stanza))

@app.route('/stanza/<codice>', methods=['GET', 'POST'])
def stanza(codice):
    ruolo = session.get('ruolo')

    if codice not in stanze:
        return "Stanza non trovata!", 404

    # Gestione chat
    if request.method == 'POST' and 'messaggio' in request.form:
        messaggio = request.form['messaggio']
        stanze[codice]["chat"].append((ruolo, messaggio))

    # Gestione numeri di telefono
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']
        stanze[codice]["numeri"][ruolo] = numero

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=stanze[codice]["chat"],
        numeri=stanze[codice]["numeri"]
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
