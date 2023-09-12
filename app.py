from flask import Flask, render_template, request, redirect, url_for
# Create a Flask instance
app = Flask(__name__)
@app.route('/')
def index():
    
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

    
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)