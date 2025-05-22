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

KEY = os.environ.get('KEY') # Ensure KEY is loaded before pysmile.License
key_list = [HexInt(int(item.strip(), 16)) for item in KEY.strip('[]').split(',')]

# Initialize PySmile License globally and once.
pysmile.License((
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
	),[
	0x13,0x27,0x92,0xab,0xe4,0xb6,0x92,0xde,0xc9,0x92,0xb2,0xb5,0x0f,0xa1,0xc3,0x97,
	0xdc,0xb8,0x80,0xc3,0x53,0xd3,0x77,0x6b,0x78,0x34,0xf4,0x43,0x37,0xe9,0x32,0x2f,
	0xc1,0x1a,0x64,0x89,0xec,0x5e,0x82,0x10,0x31,0x23,0x39,0x87,0xe0,0x80,0x09,0xf1,
	0x9f,0xb3,0x08,0x19,0xcd,0x2e,0x2b,0xfe,0x3d,0xfd,0xef,0x43,0x76,0x02,0x02,0xbc])

# Global variables for networks and cached static data
tan_net = pysmile.Network()
bn_net = pysmile.Network()

tan_node_names = []
tan_node_fullnames = {}
tan_evidence_states = {}

bn_node_names = []
bn_node_fullnames = {}
bn_evidence_states = {}

app = Flask(__name__)

# Helper function to extract static data (node names, full names, evidence states)
def pull_static_data(net):
    node_names_local = []
    node_fullnames_local = {}
    evidence_states_local = {}
    for i in range(net.get_node_count()):
        node_name = net.get_node_id(i)
        node_names_local.append(node_name)
        node_fullnames_local[node_name] = net.get_node_name(i)
        node_states = net.get_outcome_ids(node_name)
        # Apply replacements to outcome IDs
        evidence_states_local[node_name] = [val.replace('1_','1.').
                                           replace('4_','4.').
                                           replace('n_','n ').
                                           replace('w_','w ').
                                           replace('r_','r ').
                                           replace('_','-') for val in node_states]
    return node_names_local, node_fullnames_local, evidence_states_local

# Helper function to get dynamic node values (current beliefs)
def get_dynamic_node_values(net):
    evidence_values = {}
    for i in range(net.get_node_count()):
        node_name = net.get_node_id(i)
        evidence_values[node_name] = net.get_node_value(i)
    return evidence_values

# Load networks and static data at startup
@app.before_first_request
def initial_load():
    global tan_net, bn_net, \
           tan_node_names, tan_node_fullnames, tan_evidence_states, \
           bn_node_names, bn_node_fullnames, bn_evidence_states

    # Load TAN network and its static data
    tan_net.read_file('TAN.xdsl')
    tan_net.update_beliefs() 
    names, fullnames, states = pull_static_data(tan_net)
    tan_node_names.extend(names)
    tan_node_fullnames.update(fullnames)
    tan_evidence_states.update(states)

    # Load BN network and its static data
    bn_net.read_file('Stroke-best-update.xdsl')
    bn_net.update_beliefs()
    names, fullnames, states = pull_static_data(bn_net)
    bn_node_names.extend(names)
    bn_node_fullnames.update(fullnames)
    bn_evidence_states.update(states)


@app.route("/", methods=["GET"])
def home():
    return render_template("index2.html")


@app.route("/TAN", methods=["GET", "POST"])
def tan():   
    # Use global tan_net and its pre-loaded static data
    # tan_net.update_beliefs() # Beliefs are updated initially and after evidence is set.
                             # For GET, we want the current base beliefs.
    evidence_values = get_dynamic_node_values(tan_net) # Get current values
        
    if request.method == "POST":
        input_data = {
            key: float(request.form[key]) for key in request.form
        }
        result_text = "" # Renamed from 'result' to avoid conflict with any potential template variable
        tan_net.clear_all_evidence()
           
        try:
            for variable, value in input_data.items():
                node_handle = tan_net.get_node(variable)
                tan_net.set_evidence(node_handle, int(value))

            tan_net.update_beliefs()
            evidence_values = get_dynamic_node_values(tan_net) # Update values after setting evidence

            output_node = "isStroke"  
            output_handle = tan_net.get_node(output_node)
            output_probability = tan_net.get_node_value(output_handle)
            # result.append(output_probability[1]) # 'result' was a list, now directly a string
            result_text = f"Probability of getting stroke in 10 years (TAN): {round(output_probability[1],2)}"

        except SMILEException as e:
            result_text = f"Error: {e}"
        
        return render_template("tan2.html", result=result_text, nodes=tan_node_names, evidence_states=tan_evidence_states, evidence_values=evidence_values, node_fullnames=tan_node_fullnames)
    
    # For GET request
    tan_net.clear_all_evidence() # Clear any previous evidence from other sessions/requests if any
    tan_net.update_beliefs()    # Re-update to ensure fresh base beliefs
    evidence_values = get_dynamic_node_values(tan_net) # Get fresh values
    return render_template("tan2.html", nodes=tan_node_names, evidence_states=tan_evidence_states, evidence_values=evidence_values, node_fullnames=tan_node_fullnames)

@app.route("/BN", methods=["GET", "POST"])
def bn():   
    # Use global bn_net and its pre-loaded static data
    evidence_values = get_dynamic_node_values(bn_net) # Get current values
        
    if request.method == "POST":
        input_data = {
            key: float(request.form[key]) for key in request.form
        }
        result_text = ""
        bn_net.clear_all_evidence()
           
        try:
            for variable, value in input_data.items():
                node_handle = bn_net.get_node(variable)
                bn_net.set_evidence(node_handle, int(value))

            bn_net.update_beliefs()
            evidence_values = get_dynamic_node_values(bn_net) # Update values after setting evidence

            output_node = "Stroke_2"  
            output_handle = bn_net.get_node(output_node)
            output_probability = bn_net.get_node_value(output_handle)
            result_text = f"Probability of getting stroke in 10 years (BN): {round(output_probability[1],2)}"

        except SMILEException as e:
            result_text = f"Error: {e}"
        
        return render_template("bn2.html", result=result_text, nodes=bn_node_names, evidence_states=bn_evidence_states, evidence_values=evidence_values, node_fullnames=bn_node_fullnames)

    # For GET request
    bn_net.clear_all_evidence() # Clear any previous evidence
    bn_net.update_beliefs()    # Re-update to ensure fresh base beliefs
    evidence_values = get_dynamic_node_values(bn_net) # Get fresh values
    return render_template("bn2.html", nodes=bn_node_names, evidence_states=bn_evidence_states, evidence_values=evidence_values, node_fullnames=bn_node_fullnames)

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
        

        return render_template("logreg2.html", result=result, ebm=ebm, xgb=xgb, input_data=input_data)

    return render_template("logreg2.html", result=result, ebm=ebm, xgb=xgb, input_data=input_data)


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
        
        return render_template("ite2.html", Upperaf=Upperaf, Loweraf=Loweraf,
                               input_data=input_data)
    
    return render_template("ite2.html", Upperaf=Upperaf, Loweraf=Loweraf, 
                           input_data=input_data)

if __name__ == "__main__":
    app.run(debug=True)
