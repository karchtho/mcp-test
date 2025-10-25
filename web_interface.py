#!/usr/bin/env python3
from flask import Flask, request, render_template, jsonify, redirect, url_for
import pymysql
import os
from config import DATABASE_CONFIG
import markdown

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

# Créer le dossier uploads s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    return pymysql.connect(**DATABASE_CONFIG, cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cours MCP - Upload</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .upload-zone { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
            .upload-zone:hover { border-color: #999; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #005a85; }
            .cours-list { margin-top: 30px; }
            .cours-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>📚 Interface Cours MCP</h1>
        
        <div class="upload-zone">
            <h3>Upload de fichiers .md</h3>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="files" multiple accept=".md,.txt" style="margin: 10px;">
                <br><br>
                <label>Matière: <input type="text" name="matiere" placeholder="Ex: Informatique"></label>
                <br><br>
                <button type="submit">📤 Uploader les cours</button>
            </form>
        </div>
        
        <div>
            <h3>Ajout manuel</h3>
            <form action="/add_manual" method="post">
                <input type="text" name="titre" placeholder="Titre du cours" style="width: 100%; margin: 5px 0; padding: 8px;">
                <input type="text" name="matiere" placeholder="Matière" style="width: 100%; margin: 5px 0; padding: 8px;">
                <select name="type_contenu" style="width: 100%; margin: 5px 0; padding: 8px;">
                    <option value="cours">Cours</option>
                    <option value="exercice">Exercice</option>
                    <option value="corrige">Corrigé</option>
                </select>
                <textarea name="contenu" placeholder="Contenu..." style="width: 100%; height: 200px; margin: 5px 0; padding: 8px;"></textarea>
                <button type="submit">➕ Ajouter</button>
            </form>
        </div>
        
        <div class="cours-list">
            <h3>Cours existants</h3>
            <a href="/list">📋 Voir tous les cours</a>
        </div>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    matiere = request.form.get('matiere', '')
    
    connection = get_db_connection()
    uploaded_count = 0
    
    try:
        for file in files:
            if file and file.filename.endswith(('.md', '.txt')):
                # Lire le contenu
                content = file.read().decode('utf-8')
                titre = file.filename.replace('.md', '').replace('.txt', '')
                
                # Sauver en base
                with connection.cursor() as cursor:
                    sql = "INSERT INTO cours (titre, matiere, type_contenu, contenu) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (titre, matiere, 'cours', content))
                    connection.commit()
                    uploaded_count += 1
                
                # Sauver le fichier
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        return f'<h2>✅ {uploaded_count} fichier(s) uploadé(s) !</h2><a href="/">← Retour</a>'
    
    finally:
        connection.close()

@app.route('/add_manual', methods=['POST'])
def add_manual():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO cours (titre, matiere, type_contenu, contenu) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (
                request.form['titre'],
                request.form['matiere'],
                request.form['type_contenu'],
                request.form['contenu']
            ))
            connection.commit()
        return '<h2>✅ Cours ajouté !</h2><a href="/">← Retour</a>'
    finally:
        connection.close()

@app.route('/list')
def list_courses():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM cours ORDER BY date_ajout DESC")
            courses = cursor.fetchall()
        
        html = '<h1>📚 Liste des cours</h1><a href="/">← Retour</a><br><br>'
        for course in courses:
            html += f'''
            <div style="border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px;">
                <h3>{course["titre"]}</h3>
                <p><strong>Matière:</strong> {course["matiere"] or "Non définie"} | 
                   <strong>Type:</strong> {course["type_contenu"]} | 
                   <strong>Date:</strong> {course["date_ajout"]}</p>
                <p>{course["contenu"][:300]}...</p>
            </div>
            '''
        return html
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)