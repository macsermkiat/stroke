import joblib
import numpy as np
import pandas as pd
#import sklearn
#from sklearn.compose import ColumnTransformer
from xgboost import XGBClassifier
import gc
#from interpret.glassbox import ExplainableBoostingClassifier


def logreg_function(input_data):
    
    loaded_model = joblib.load('LogReg.pkl')
    std = joblib.load('std101.pkl')
    ebm = joblib.load('ebm_all.pkl')
    xgb = XGBClassifier()
    xgb.load_model('xgb_allstroke.json')    
    input_data = pd.DataFrame([input_data])
    ebm_prob = ebm.predict_proba(input_data)
    xgb_prob = xgb.predict_proba(input_data.values)
    input_data.iloc[:,1:6] = input_data.iloc[:,1:6].astype('category')
    input_data.iloc[:,8:14] = input_data.iloc[:,8:14].astype('category')
    is_cat = np.array([dt.kind == 'O' for dt in input_data.dtypes])
    num_cols = input_data.columns.values[~is_cat]
    input_data[num_cols] = std.transform(input_data[num_cols].values)  
    y_prob = loaded_model.predict_proba(input_data)
    ebm_pred=ebm_prob[0]
    xgb_pred=xgb_prob[0][1]
    #ebm_pred =['HIGH' if x>0.467 else 'LOW' for x in [ebm_prob[0][1]]]
    #xgb_pred =['HIGH' if x>0.445 else 'LOW' for x in [xgb_prob[0][1]]]

    del input_data,std,ebm,xgb,loaded_model
    gc.collect()
    return y_prob[0][1], ebm_pred[1], xgb_pred

'''
ct = ColumnTransformer(transformers=[('cat', OneHotEncoder(), cat_cols)], remainder='passthrough')
steps = [('ct',ct)]
xgb = XGBClassifier(use_label_encoder=False, eval_metric = 'logloss')
booster = xgboost.Booster()
booster.load_model('xgb_allstroke.json')
xgb._Booster = booster
'''