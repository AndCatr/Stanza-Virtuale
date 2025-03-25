from flask import Flask, render_template, request, redirect, url_for, jsonify
import random, string, time

app = Flask(__name__)

stanze = {}

def genera_codice():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        codice = genera_codice()
        stanze[codice] = {
            'chat': [],
            'numero_penelope': '',
            'numero_eric': '',
            'blocco_chat': False,
            'blocco_numero_penelope': False,
            'blocco_numero_eric': False,
            'countdown_attivo': False,
            'countdown_inizio': 0
        }
        print(f"✅ Creazione stanza: {codice}")
        return render_template('ingresso.html', codice=codice)
    return render_template('index.html')

@app.route('/ingresso', methods=['POST'])
def ingresso():
    codice = request.form['codice'].strip().upper()
    if codice in stanze:
        stanza = stanze[codice]
        if 'penelope_entrata' not in stanza:
            stanza['penelope_entrata'] = True
            ruolo = "Penelope"
        elif 'eric_entrata' not in stanza:
            stanza['eric_entrata'] = True
            ruolo = "Eric"
        else:
            return "Stanza piena"
        return redirect(url_for('stanza', codice=codice, ruolo=ruolo))
    return "Codice stanza non trovato"

@app.route('/stanza/<codice>', methods=['GET', 'POST'])
def stanza(codice):
    ruolo = request.args.get('ruolo')
    stanza = stanze.get(codice)

    if not stanza:
        return "Stanza non trovata"

    if request.method == 'POST':
        if 'messaggio' in request.form:
            messaggio = request.form['messaggio'].strip()
            if messaggio:
                stanza['chat'].append((ruolo, messaggio))
        elif 'numero' in request.form:
            numero = request.form['numero'].strip()
            if ruolo == "Penelope" and stanza['numero_penelope'] == '':
                stanza['numero_penelope'] = numero
                stanza['blocco_numero_penelope'] = True
            elif ruolo == "Eric" and stanza['numero_eric'] == '':
                stanza['numero_eric'] = numero
                stanza['blocco_numero_eric'] = True
            if stanza['numero_penelope'] and stanza['numero_eric'] and not stanza['countdown_attivo']:
                stanza['countdown_attivo'] = True
                stanza['countdown_inizio'] = time.time()

    return render_template("stanza.html",
                           codice=codice,
                           ruolo=ruolo,
                           chat=stanza['chat'])

@app.route('/aggiorna_chat/<codice>')
def aggiorna_chat(codice):
    stanza = stanze.get(codice)
    return jsonify(chat=stanza['chat'])

@app.route('/aggiorna_numeri/<codice>')
def aggiorna_numeri(codice):
    stanza = stanze.get(codice)
    return jsonify(
        numero_penelope=stanza['numero_penelope'],
        numero_eric=stanza['numero_eric']
    )

@app.route('/controlla_blocco/<codice>')
def controlla_blocco(codice):
    stanza = stanze.get(codice)
    return jsonify(
        blocco_chat=stanza['blocco_chat'],
        blocco_numero_penelope=stanza['blocco_numero_penelope'],
        blocco_numero_eric=stanza['blocco_numero_eric']
    )

@app.route('/verifica_countdown/<codice>')
def verifica_countdown(codice):
    stanza = stanze.get(codice)
    if stanza['countdown_attivo']:
        tempo_passato = time.time() - stanza['countdown_inizio']
        if tempo_passato >= 30:
            stanza['blocco_chat'] = True
            return jsonify(distrutta=True)
        else:
            return jsonify(distrutta=False, tempo=round(30 - tempo_passato))
    return jsonify(distrutta=False)

@app.route('/autodistrutta')
def autodistrutta():
    return render_template("autodistrutta.html")

@app.route('/email/<codice>')
def email_rossi(codice):
    return render_template("email.html", codice=codice)

if __name__ == '__main__':
    app.run(debug=True)
