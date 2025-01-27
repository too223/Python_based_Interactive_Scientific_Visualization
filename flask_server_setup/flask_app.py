#flask app

from flask import Flask, render_template
from bokeh.client import pull_session
from bokeh.embed import server_document

#instantiate the flask app
app = Flask(__name__)

#create index page function
@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")

@app.route("/sliders_reaction_kinetics", methods=['GET'])
def sliders_reaction_kinetics():
    #bokeh_script_sliders_reaction_kinetics = server_document(url="http://localhost:5006/sliders_reaction_kinetics")
    bokeh_script_sliders_reaction_kinetics = server_document(url="https://srrweb.cc.lehigh.edu/sliders_reaction_kinetics")
    return render_template("sliders_reaction_kinetics.html", bokeh_script_sliders_reaction_kinetics=bokeh_script_sliders_reaction_kinetics)

@app.route("/ZECC", methods=['GET'])
def ZECC():
    #bokeh_script_ZECC = server_document(url="http://localhost:5007/ZECC")
    bokeh_script_ZECC = server_document(url="https://srrweb.cc.lehigh.edu/ZECC")
    return render_template("ZECC.html", bokeh_script_ZECC=bokeh_script_ZECC)

@app.route("/SIR", methods=['GET'])
def SIR():
    #bokeh_script_SIR = server_document(url="http://localhost:5008/SIR")
    bokeh_script_SIR = server_document(url="https://srrweb.cc.lehigh.edu/SIR")
    return render_template("SIR.html", bokeh_script_SIR=bokeh_script_SIR)

@app.route("/catalysis_data_interactive_visualization", methods=['GET'])
def catalysis_data_interactive_visualization():
    #bokeh_script_catalysis_data_interactive_visualization = server_document(url="http://localhost:5009/catalysis_data_interactive_visualization")
    bokeh_script_catalysis_data_interactive_visualization = server_document(url="https://srrweb.cc.lehigh.edu/catalysis_data_interactive_visualization")
    return render_template("catalysis.html", bokeh_script_catalysis_data_interactive_visualization=bokeh_script_catalysis_data_interactive_visualization)

@app.route("/acknowledgements", methods=['GET'])
def acknowledgements():
    return render_template("acknowledgements.html")

#run the app
if __name__ == "__main__":
    app.run(port=8080)
 
