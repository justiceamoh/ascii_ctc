# Description: Script to test Lasagne - CTC using toy ascii alphabet data from @rakeshvar
# Dependencies: print_utils.py, data.pkl (ascii scribe) from rakeshvar's repo

import pickle as pkl
import numpy as np
import time
import theano
import theano.tensor as T
import lasagne
import lasagne.layers as L
import ctc_cost

from lasagne.layers import InputLayer, LSTMLayer, ReshapeLayer, DenseLayer, GaussianNoiseLayer, NonlinearityLayer, GRULayer
from print_utils import slab_print, prediction_printer

# Training Params 
LEARNING_RATE = 0.001
N_BATCH = 5
NUM_EPOCHS = 1

# Number of units in the hidden (recurrent) layer
L1_UNITS = 64
L2_UNITS = 64

#### Load Ascii Toy Data File from rakeshvar ####
filename = 'data.pkl'
with open(filename,"rb") as pkl_file:
	data = pkl.load(pkl_file)


chars = data['chars']
nClasses = len(chars)
nDims = len(data['x'][0])
nSamples = len(data['x'])
nTrainSamples = int(nSamples * .75)
labels_print, labels_len = prediction_printer(chars)


data_x = []
data_y = []

for x, y in zip(data['x'], data['y']):
   # Insert blanks at alternate locations in the labelling (blank is nClasses)
#    y1 = [nClasses] + y + [nClasses]
	# y1 = [nClasses]
	y1 = y   
	# for char in y:
	# 	y1 += [char, nClasses]

	data_y.append(np.asarray(y1, dtype=np.int32))
	data_x.append(np.asarray(x,  dtype=theano.config.floatX))
	pass


print("Printing sample input ...")
idx = 0 
slab_print(data_x[idx])
chars.append(' ') 
print(data_y[idx], "".join(chars[i] for i in data_y[idx]))


# Convert list of input sequences to zero-padded 3D array
num_feat   = data_x[0].shape[0]
#max_x_len  = np.max([bb.shape[1] for bb in data_x])  #list comprehension to get all lengths
max_x_len  = 20
x          = np.zeros([len(data_x), max_x_len, num_feat])
for i, examples in enumerate(data_x):
    for j, feat in enumerate(examples):
        for k, seq in enumerate(feat):
            if k<max_x_len:
                x[i][k][j]=seq
            
            

# Convert list of target sequences to zero-padded 2D array
max_y_len = max(map(len,data_y))
y=np.zeros([len(data_y), max_y_len],dtype=np.int32)
#y=np.ones([len(data_y), max_y_len])*95
for i, examples in enumerate(data_y):
    for j, seq in enumerate(examples):
        y[i][j]=seq
        
        


## LSTM Network Architecture
num_batch     = None
input_seq_len = None
num_feat      = num_feat
num_classes   = nClasses + 1

soft = lasagne.nonlinearities.softmax
tanh = lasagne.nonlinearities.tanh
identity = lasagne.nonlinearities.identity

l_in = InputLayer(shape=(num_batch, input_seq_len, num_feat))
batchsize, seqlen, _ = l_in.input_var.shape

l_noise = GaussianNoiseLayer(l_in, sigma=0.6) 
# l_mask  = InputLayer(shape=(batchsize, seqlen))
# l_rnn_1 = LSTMLayer(l_noise, num_units=L1_UNITS, mask_input=l_mask)
l_rnn_1 = GRULayer(l_noise, num_units=L1_UNITS)
l_rnn_2 = GRULayer(l_rnn_1, num_units=L2_UNITS)
l_shp   = ReshapeLayer(l_rnn_2,(-1, L2_UNITS))
l_out   = DenseLayer(l_shp, num_units=num_classes, nonlinearity=identity)
l_out_shp  = ReshapeLayer(l_out, (batchsize, seqlen, num_classes)) 

l_out_softmax = NonlinearityLayer(l_out, nonlinearity=soft)
l_out_softmax_shp = ReshapeLayer(l_out_softmax,(batchsize, seqlen, num_classes))


output_lin_ctc = L.get_output(l_out_shp)
network_output = L.get_output(l_out_softmax_shp)
all_params = L.get_all_params(l_rnn_2, trainable=True)


# Cost functions
target_values = T.imatrix('target_output')
input_values  = T.imatrix()

### Gradients ###
# pseudo costs - ctc cross entropy b/n targets and linear output - used in training
pseudo_cost = ctc_cost.pseudo_cost(target_values, output_lin_ctc)
pseudo_cost_grad = T.grad(pseudo_cost.sum() / batchsize, all_params)
pseudo_cost = pseudo_cost.mean()

# true costs
cost = ctc_cost.cost(target_values, network_output)
cost = cost.mean()

## debugging cost functions
# xx = X_test[:100]
# yy = y_test[:100]
# yy = yy.reshape(yy.shape[0],1)
# ww = network_output.eval({l_in.input_var:xx})
# ll = output_lin_ctc.eval({l_in.input_var:xx})
# cc = cost.eval({target_values:yy,l_in.input_var:xx}
# pc = pseudo_cost.eval({target_values:yy,l_in.input_var:xx}


# Compute SGD updates for training
print("Computing updates ...")
updates = lasagne.updates.rmsprop(pseudo_cost_grad, all_params, LEARNING_RATE)

# Theano functions for training and computing cost
print("Compiling functions ...")
train = theano.function(
    [l_in.input_var, target_values], [cost, pseudo_cost, network_output], updates=updates)
validate = theano.function([l_in.input_var, target_values], [cost, network_output]) 
predict  = theano.function([l_in.input_var], network_output)



###############
### TRAINING ##
###############


#### Training Network ####
print("Training network ...")
num_batches_train = int(np.ceil(len(x) / N_BATCH))
split_ratio = 0.7*num_batches_train

for epoch in range(NUM_EPOCHS):
	now = time.time
	tlosses = []
	vlosses = []
	plosses = []
	probabilities = []

	traindata = zip(x,y)
	np.random.shuffle(traindata)
	sequences, labels = zip(*traindata)


	for batch in range(num_batches_train):
		batch_slice = slice(N_BATCH * batch, N_BATCH * (batch + 1))
		if batch < split_ratio:
			xi = sequences[batch_slice]
			yi = labels[batch_slice]

			loss, ploss, probs = train(xi,yi)
			tlosses.append(loss)
			plosses.append(ploss)
		else:
			loss, probs = validate(xi,yi)
			y_pred = np.argmax(probs, axis=-1)
			vlosses.append(loss)
			probabilities.append(probs)

		print("Batch {0}/{1}, loss:{2:.6}, ploss:{3:.6}".format(batch,num_batches_train,loss,ploss))

# Print test example and label sequence
idx=0
slab_print(xi[idx].T)
print(yi[idx], "".join(chars[i] for i in yi[idx]))

# Predict test label sequence
probs  = predict(xi)
y_pred = np.argmax(probs, axis=-1)
print(y_pred[idx], "".join(chars[i] for i in y_pred[idx]))



