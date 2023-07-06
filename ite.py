import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
import datetime 
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import load_model
from Dragon import EpsilonLayer, Base_Loss, TarReg_Loss

def predict_model(input_data):
    modelU = load_model('dragonnet_pl_975.h5', 
                   custom_objects={'EpsilonLayer':EpsilonLayer,
                                  'TarReg_Loss':TarReg_Loss,
                                  'regression_loss':Base_Loss.regression_loss,
                                  'treatment_acc':Base_Loss.treatment_acc})
    modelL = load_model('dragonnet_pl_025.h5', 
                   custom_objects={'EpsilonLayer':EpsilonLayer,
                                  'TarReg_Loss':TarReg_Loss,
                                  'regression_loss':Base_Loss.regression_loss,
                                  'treatment_acc':Base_Loss.treatment_acc})
    modelM = load_model('dragonnet_pl_mn.h5', 
                   custom_objects={'EpsilonLayer':EpsilonLayer,
                                  'TarReg_Loss':TarReg_Loss,
                                  'regression_loss':Base_Loss.regression_loss,
                                  'treatment_acc':Base_Loss.treatment_acc})
    sc = joblib.load('ite_scaler.joblib')
    
    input_data = pd.DataFrame([input_data], columns=['DLP','HT','AF','age',
                                                    'DM','BMIcalc','GFR','antiPL'])
    
    antiPL = input_data['antiPL']
    input_data = input_data.drop(['antiPL'], axis=1)
    input_data = sc.transform(input_data.values.reshape(1,-1))
    lower = modelL.predict(input_data)
    upper = modelU.predict(input_data)
    mean = modelM.predict(input_data)
    
    return lower,upper, mean, antiPL

def logistic_sigmoid(x):
    return 1/(1+(np.exp(-x)))
def T0(x):
    return (1-logistic_sigmoid(x))/logistic_sigmoid(x)
def T1(x):
    return logistic_sigmoid(x)/(1-logistic_sigmoid(x))

def ite_function(input_data):
    #Numbers from training and validation
    neu0 = 0.01254
    neu1 = 0.00657
    
    LO = []
    HI = []
    lower, upper, mn, antiPL = predict_model(input_data)  

    for i in [0,1]:
        tmp = pd.DataFrame([lower[0,i],upper[0,i]]).T
        tmp['x']=mn[0,i]
        Lo = tmp[0]-neu0
        Hi = tmp[1]+neu1
        tmp['V'] = np.max([tmp['x']-Lo,Hi-tmp['x']],axis=0)
        neu = np.quantile(tmp['V'],0.9)
        Lo = tmp[0]-neu
        Hi = tmp[1]+neu
        LO.append(Lo)
        HI.append(Hi)

    if antiPL[0]==0:
        Upperaf = HI[1]-LO[0]
        Loweraf = LO[1]-HI[0]
    elif antiPL[0]==1:
        Upperaf = HI[0]-LO[1]
        Loweraf = LO[0]-HI[1]
    else: 
        print("ERROR")

    return Upperaf.values[0], Loweraf.values[0]

