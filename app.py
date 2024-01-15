from flask import Flask, render_template, url_for, request

#initialize app
app = Flask(__name__)

#index route
@app.route('/', methods=['POST', 'GET'])
def index():
    #if user enters input
    if request.method == "POST":
        #get user input playlist name
        PlName = request.form.get('PlName', '')

        #if name is not empty
        if PlName:
            print(f"Playlist name: {PlName}")
        
        #if name is empty
        else:
            print("Playlist name does not exit")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)