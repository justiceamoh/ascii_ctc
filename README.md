## Lasagne Port of a Recurrent Neural Network with Connectionist Temporal Classification
This is a lasagne implementation of the [the rnn-ctc implementation](https://github.com/rakeshvar/rnn_ctc) by @rakeshvar.

The [original lasagne port](https://github.com/skaae/Lasagne-CTC) is by @skaae (Søren Kaae Sønderby). The implementation here attempts to use that ctc source on the toy ascii dataset from @rakeshvar's repo. 


## Usage
- *gen_ascii.sh* : bash script to generate training data
- *test_load.sh* : python script to train rnn_ctc on data
- *ascii_ctc_lasagne.ipynb* : an ipython notebook implementing rnn_ctc training


