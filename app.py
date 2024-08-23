from flask import Flask, render_template, send_file, abort
import os

app = Flask(__name__)

ROOT_DIR = 'files'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<category>')
def category_page(category):
    if category not in ['FE', 'SE', 'TE', 'BE']:
        abort(404)
    return render_template(f'{category.lower()}.html', category=category)

@app.route('/<category>/files/<path:subpath>')
def browse_files(category, subpath):
    if category not in ['FE', 'SE', 'TE', 'BE']:
        abort(404)
    
    full_path = os.path.join(ROOT_DIR, category, subpath)
    
    if not os.path.exists(full_path):
        abort(404)
    
    if os.path.isfile(full_path):
        return send_file(full_path, as_attachment=True)
    
    if os.path.isdir(full_path):
        contents = os.listdir(full_path)
        return render_template('browse.html', 
                               contents=contents, 
                               current_path=f'{category}/files/{subpath}', 
                               category=category)

if __name__ == '__main__':
    app.run(debug=True)