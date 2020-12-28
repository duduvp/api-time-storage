# !/usr/bin/python
import json
import psycopg2
from configparser import ConfigParser
from flask import Flask, request, Response
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api

app = Flask(__name__)
auth = HTTPBasicAuth()
api = Api(app)


@auth.verify_password
def verify_password(username, password):
    return username == 'apitimestorage' and password == '_@P1t1m3$t0r4g3##/'


@app.route('/')
@auth.login_required
def index():
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT version()')
    db_version = cur.fetchone()
    close(conn)
    return '<h3>API TimeStorage Running!</h3><h4>PostgreSQL DB Version: ' + str(db_version) + '</h4>'


@app.route('/autor', methods=['GET'])
@auth.login_required
def autor():
    query = "SELECT * FROM autor ORDER BY status_autor ASC, nome_autor ASC"
    result = query_db(query, False)
    return json.dumps(result, indent=4, sort_keys=True, default=str)


@app.route('/cadastrar', methods=['POST'])
@auth.login_required
def cadastrar():
    if not request.json:
        return 'Os dados do JSON não podem estar vazios!', 400
    data = request.get_json()
    conn = connect()
    cur = conn.cursor()
    query = "SELECT fn_register_user('" + data['nome_pessoa'] + "','" + data['sobrenome_pessoa'] + "','" + \
            data['email_pessoa'] + "','" + data['telefone_pessoa'] + "','" + data['data_nascimento_pessoa'] + "','" + \
            data['senha_usuario'] + "')"
    cur.execute(query)
    resp = cur.fetchone()[0]
    if resp:
        conn.commit()
        close(conn)
        return Response("{'message': 'Usuário cadastrado com sucesso!'}", status=201, mimetype='application/json')
    else:
        conn.rollback()
        close(conn)
        return Response("{'message': 'Problemas ao cadastrar usuário!'}", status=500, mimetype='application/json')


@app.route('/categoria', methods=['GET'])
@auth.login_required
def categoria():
    query = "SELECT * FROM categoria ORDER BY status_categoria ASC, descricao_categoria ASC"
    result = query_db(query, False)
    return json.dumps(result)


@app.route('/dashboard', methods=['GET'])
@auth.login_required
def dashboard():
    query = "SELECT * FROM v_dashboard"
    result = query_db(query, False)
    return json.dumps(result)


@app.route('/documentos', methods=['GET'])
@auth.login_required
def documentos():
    query = "SELECT * FROM v_docs"
    result = query_db(query, False)
    return json.dumps(result, indent=4, sort_keys=True, default=str)


@app.route('/documentos/<int:cod>', methods=['GET'])
@auth.login_required
def documentos_detail(cod):
    query = "SELECT * FROM v_docs_info WHERE id_documento = " + str(cod)
    result = query_db(query, False)
    return json.dumps(result, indent=4, sort_keys=True, default=str)


@app.route('/imagens/<int:cod>', methods=['GET'])
@auth.login_required
def imagens(cod):
    query = "SELECT * FROM imagem WHERE id_documento = " + str(cod)
    result = query_db(query, False)
    return json.dumps(result)


@app.route('/editora', methods=['GET'])
@auth.login_required
def editora():
    query = "SELECT * FROM editora ORDER BY status_editora ASC, descricao_editora ASC"
    result = query_db(query, False)
    return json.dumps(result)


@app.route('/envautor', methods=['POST'])
@auth.login_required
def envautor():
    if not request.json:
        return 'Os dados do JSON não podem estar vazios!', 400
    data = request.get_json()
    conn = connect()
    cur = conn.cursor()
    query = "INSERT INTO autor (nome_autor, data_nascimento_autor, data_falecimento_autor) VALUES ('" + data[
        'nome_autor'] + "','" + data['data_nascimento_autor'] + "','" + data['data_falecimento_autor'] + "')"
    cur.execute(query)
    conn.commit()
    close(conn)
    return Response("{'message': 'Autor cadastrado com sucesso!'}", status=201, mimetype='application/json')


@app.route('/envcategoria', methods=['POST'])
@auth.login_required
def envcategoria():
    if not request.json:
        return 'Os dados do JSON não podem estar vazios!', 400
    data = request.get_json()
    conn = connect()
    cur = conn.cursor()
    query = "INSERT INTO categoria (descricao_categoria) VALUES ('" + data['descricao_categoria'] + "')"
    cur.execute(query)
    conn.commit()
    close(conn)
    return Response("{'message': 'Categoria cadastrada com sucesso!'}", status=201, mimetype='application/json')


@app.route('/enveditora', methods=['POST'])
@auth.login_required
def enveditora():
    if not request.json:
        return 'Os dados do JSON não podem estar vazios!', 400
    data = request.get_json()
    conn = connect()
    cur = conn.cursor()
    query = "INSERT INTO editora (descricao_editora) VALUES ('" + data['descricao_editora'] + "')"
    cur.execute(query)
    conn.commit()
    close(conn)
    return Response("{'message': 'Editora cadastrada com sucesso!'}", status=201, mimetype='application/json')


@app.route('/envgenero', methods=['POST'])
@auth.login_required
def envgenero():
    if not request.json:
        return 'Os dados do JSON não podem estar vazios!', 400
    data = request.get_json()
    conn = connect()
    cur = conn.cursor()
    query = "INSERT INTO genero (descricao_genero) VALUES ('" + data['descricao_genero'] + "')"
    cur.execute(query)
    conn.commit()
    close(conn)
    return Response("{'message': 'Gênero cadastrado com sucesso!'}", status=201, mimetype='application/json')


@app.route('/login', methods=['POST'])
@auth.login_required
def login():
    if not request.json:
        return 'Os dados do JSON não podem estar vazios!', 400
    data = request.get_json()
    email = data['email']
    senha = data['senha']
    if email is None or senha is None:
        return 'Dados de e-mail ou senha não podem ser vazios!', 400
    query = "SELECT * FROM v_login WHERE email_pessoa = '" + email + "' AND senha_usuario = '" + senha + "'"
    conn = connect()
    cur = conn.cursor()
    cur.execute(query)
    if cur.rowcount <= 0:
        return 'Usuário ou senha inválidos!', 404
    records = cur.fetchall()
    user = User()
    for row in records:
        user.cod = row[0]
        user.nome = row[1]
        user.email = row[2]
        user.tipo = row[3]
    close(conn)
    return json.dumps(user.__dict__)


class Document:
    def __init__(self, cod=-1, titulo='', sinopse='', publicacao='', categoria='', editora=''):
        self.cod = cod
        self.titulo = titulo
        self.sinopse = sinopse
        self.publicacao = publicacao
        self.categoria = categoria
        self.editora = editora


class User:
    def __init__(self, cod=-1, nome='', email='', tipo=-1):
        self.cod = cod
        self.nome = nome
        self.email = email
        self.tipo = tipo


def query_db(query, one=False):
    conn = connect()
    cur = conn.cursor()
    cur.execute(query)
    r = [dict((cur.description[i][0], value) \
              for i, value in enumerate(row)) for row in cur.fetchall()]
    close(conn)
    return (r[0] if r else None) if one else r


def config(filename='util/database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


def connect():
    try:
        params = config()
        conn = psycopg2.connect(**params)
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


def close(conn):
    if conn is not None:
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0')
