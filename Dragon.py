import tensorflow as tf
from tensorflow.keras.layers import Layer
from tensorflow.keras.losses import Loss
class EpsilonLayer(Layer):

    def __init__(self, **kwargs):
        super(EpsilonLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        # Create a trainable weight variable for this layer.
        self.epsilon = self.add_weight(name='epsilon',
                                       shape=[1, 1],
                                       initializer='RandomNormal',
                                       #  initializer='ones',
                                       trainable=True)
        super(EpsilonLayer, self).build(input_shape)  # Be sure to call this at the end

    def call(self, inputs, **kwargs):
        #note there is only one epsilon were just duplicating it for conformability
        return self.epsilon * tf.ones_like(inputs)[:, 0:1]
    
class Base_Loss(Loss):
    #initialize instance attributes
    def __init__(self, alpha=1.0, **kwargs):
        super().__init__(**kwargs)
        self.alpha = alpha
        self.name='standard_loss'

    def split_pred(self,concat_pred):
        #generic helper to make sure we dont make mistakes
        preds={}
        preds['y0_pred'] = concat_pred[:, 0]
        preds['y1_pred'] = concat_pred[:, 1]
        preds['t_pred'] = concat_pred[:, 2]
        preds['phi'] = concat_pred[:, 3:]
        return preds

    #for logging purposes only
    def treatment_acc(self,concat_true,concat_pred):
        t_true = concat_true[:, 1]
        p = self.split_pred(concat_pred)
        #Since this isn't used as a loss, I've used tf.reduce_mean for interpretability
        return tf.reduce_mean(binary_accuracy(t_true, tf.math.sigmoid(p['t_pred']), threshold=0.5))

    def treatment_bce(self,concat_true,concat_pred):
        t_true = concat_true[:, 1]
        p = self.split_pred(concat_pred)
        lossP = tf.reduce_sum(binary_crossentropy(t_true,p['t_pred'],from_logits=True))
        return lossP
    '''
    def regression_loss(self,concat_true,concat_pred):
        y_true = concat_true[:, 0]
        t_true = concat_true[:, 1]
        p = self.split_pred(concat_pred)
        loss0 = tf.reduce_sum((1. - t_true) * tf.square(y_true - p['y0_pred']))
        loss1 = tf.reduce_sum(t_true * tf.square(y_true - p['y1_pred']))
        return loss0+loss1
    '''
    #Use pinball loss (in the name of regression loss)
    def regression_loss(self,concat_true,concat_pred):
        tau = 0.975
        y_true = concat_true[:, 0]
        t_true = concat_true[:, 1]
        p = self.split_pred(concat_pred)
        loss0 = (1.-t_true) * tf.maximum(tau * (y_true - p['y0_pred']), 
                (tau - 1) * (y_true - p['y0_pred']))
        loss1 = t_true * tf.maximum(tau * (y_true - p['y1_pred']), 
                (tau - 1) * (y_true - p['y1_pred']))
        return loss0+loss1
        
        
    def standard_loss(self,concat_true,concat_pred):
        lossR = self.regression_loss(concat_true,concat_pred)
        lossP = self.treatment_bce(concat_true,concat_pred)
        return lossR + self.alpha * lossP

    #compute loss
    def call(self, concat_true, concat_pred):        
        return self.standard_loss(concat_true,concat_pred)
    

class TarReg_Loss(Base_Loss):
    #initialize instance attributes
    def __init__(self, alpha=1,beta=1, **kwargs):
        super().__init__(**kwargs)
        self.alpha = alpha
        self.beta=beta
        self.name='tarreg_loss'

    def split_pred(self,concat_pred):
        #generic helper to make sure we dont make mistakes
        preds={}
        preds['y0_pred'] = concat_pred[:, 0]
        preds['y1_pred'] = concat_pred[:, 1]
        preds['t_pred'] = concat_pred[:, 2]
        preds['epsilon'] = concat_pred[:, 3] #we're moving epsilon into slot three
        preds['phi'] = concat_pred[:, 4:]
        return preds

    def calc_hstar(self,concat_true,concat_pred):
        #step 2 above
        p=self.split_pred(concat_pred)
        y_true = concat_true[:, 0]
        t_true = concat_true[:, 1]

        t_pred = tf.math.sigmoid(concat_pred[:, 2])
        t_pred = (t_pred + 0.001) / 1.002 # a little numerical stability trick implemented by Shi
        y_pred = t_true * p['y1_pred'] + (1 - t_true) * p['y0_pred']

        #calling it cc for "clever covariate" as in SuperLearner TMLE literature
        cc = t_true / t_pred - (1 - t_true) / (1 - t_pred)
        h_star = y_pred + p['epsilon'] * cc
        return h_star

    def call(self,concat_true,concat_pred):
        y_true = concat_true[:, 0]

        standard_loss=self.standard_loss(concat_true,concat_pred)
        h_star=self.calc_hstar(concat_true,concat_pred)
        #step 3 above
        targeted_regularization = tf.reduce_sum(tf.square(y_true - h_star))

        # final
        loss = standard_loss + self.beta * targeted_regularization
        return loss