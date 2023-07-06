from flask import Flask, render_template, request, redirect, url_for
from logreg import logreg_function
from ite import ite_function
import pandas as pd
import pysmile
from pysmile import SMILEException
import os
import sys

class HexInt(int):
    def __repr__(self):
        return hex(self)
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

KEY = os.environ.get('KEY')
key_list = [HexInt(int(item.strip(), 16)) for item in KEY.strip('[]').split(',')]
pysmile.License(((
	b"SMILE LICENSE e5ca1ad4 bbb82a84 a6e90038 "
	b"THIS IS AN ACADEMIC LICENSE AND CAN BE USED "
	b"SOLELY FOR ACADEMIC RESEARCH AND TEACHING, "
	b"AS DEFINED IN THE BAYESFUSION ACADEMIC "
	b"SOFTWARE LICENSING AGREEMENT. "
	b"Serial #: dafatg2jml3x61km3b5oej22n "
	b"Issued for: SERMKIAT LOLAK (sermkiat.lol@student.mahidol.edu) "
	b"Academic institution: Faculty of Medicine, Ramathibodi hospital, Mahidol university "
	b"Valid until: 2023-10-27 "
	b"Issued by BayesFusion activation server"
	)),key_list)



# Get the node names and evidence states

def pull_data(net):
    node_names = []
    node_fullnames = {}
    evidence_states = {}
    evidence_values = {}
    for i in range(net.get_node_count()):
        node_name = net.get_node_id(i)
        node_names.append(node_name)
        node_fullnames[node_name] = net.get_node_name(i)
        node_states = net.get_outcome_ids(node_name)
        node_values = net.get_node_value(i)
        evidence_states[node_name] = node_states
        for key in evidence_states.keys():
            evidence_states[key]=[val.replace('1_','1.').
            replace('4_','4.').
            replace('n_','n ').
            replace('w_','w ').
            replace('r_','r ').
            replace('_','-') for val in evidence_states[key]]
        evidence_values[node_name] = node_values
    return node_names, node_fullnames, evidence_states, evidence_values
    

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/TAN", methods=["GET", "POST"])


               
def tan():   
    net = pysmile.Network()
    net.read_file('TAN.xdsl')
    net.update_beliefs()
    node_names, node_fullnames, evidence_states, evidence_values = pull_data(net)
        
    if request.method == "POST":
        
        # Get input values from the form
        input_data = {
            key: float(request.form[key]) for key in request.form
        }

        # Calculate the output probability using SMILE and the Bayesian network
        result = []
        net.clear_all_evidence()
           
        try:
            for variable, value in input_data.items():
                node_handle = net.get_node(variable)
                net.set_evidence(node_handle, int(value))

            net.update_beliefs()
            node_names, node_fullnames, evidence_states, evidence_values = pull_data(net)

            # Extract the output probability
            output_node = "isStroke"  
            output_handle = net.get_node(output_node)
            output_probability = net.get_node_value(output_handle)
            result.append(output_probability[1])
            result = f"Probability of getting stroke in 10 years (TAN): {round(output_probability[1],2)}"

        except SMILEException as e:
            result = f"Error: {e}"
        
        return render_template("tan.html", result=result, nodes=node_names, evidence_states=evidence_states, evidence_values=evidence_values, node_fullnames=node_fullnames)

    return render_template("tan.html", nodes=node_names, evidence_states=evidence_states, evidence_values=evidence_values, node_fullnames=node_fullnames)

@app.route("/BN", methods=["GET", "POST"])
               
def bn():   
    net = pysmile.Network()
    net.read_file('Stroke-best-update.xdsl')
    net.update_beliefs()
    node_names, node_fullnames, evidence_states, evidence_values = pull_data(net)
        
    if request.method == "POST":
        
        # Get input values from the form
        input_data = {
            key: float(request.form[key]) for key in request.form
        }

        # Calculate the output probability using SMILE and the Bayesian network
        result = []
        net.clear_all_evidence()
           
        try:
            for variable, value in input_data.items():
                node_handle = net.get_node(variable)
                net.set_evidence(node_handle, int(value))

            net.update_beliefs()
            node_names, node_fullnames, evidence_states, evidence_values = pull_data(net)

            # Extract the output probability
            output_node = "Stroke_2"  
            output_handle = net.get_node(output_node)
            output_probability = net.get_node_value(output_handle)
            result.append(output_probability[1])
            result = f"Probability of getting stroke in 10 years (BN): {round(output_probability[1],2)}"

        except SMILEException as e:
            result = f"Error: {e}"
        
        return render_template("bn.html", result=result, nodes=node_names, evidence_states=evidence_states, evidence_values=evidence_values, node_fullnames=node_fullnames)

    return render_template("bn.html", nodes=node_names, evidence_states=evidence_states, evidence_values=evidence_values, node_fullnames=node_fullnames)

@app.route("/logreg", methods=["GET", "POST"])

def logreg():
    input_data = {}
    result = None
    ebm = None
    xgb = None
    
    if request.method == "POST":

        for key in request.form:
                input_data[key] = float(request.form[key])
        
        

        # Call the logreg_function from logreg.py with the input_data
        result, ebm, xgb = logreg_function(input_data)
        

        return render_template("logreg.html", result=result, ebm=ebm, xgb=xgb, input_data=input_data)

    return render_template("logreg.html", result=result, ebm=ebm, xgb=xgb, input_data=input_data)


@app.route("/ite", methods=["GET", "POST"])

def ite():   
    input_data = {}
    Upperaf = None    
    Loweraf = None
    if request.method == "POST":
        
        # Get input values from the form
        for key in request.form:
                input_data[key] = float(request.form[key])

                
        # Call the ite_function from ite.py with the input_data
        Upperaf, Loweraf = ite_function(input_data)
        
        return render_template("ite.html", Upperaf=Upperaf, Loweraf=Loweraf,
                               input_data=input_data)
    
    return render_template("ite.html", Upperaf=Upperaf, Loweraf=Loweraf, 
                           input_data=input_data)

if __name__ == "__main__":
    app.run(debug=True)
