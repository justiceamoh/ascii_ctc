#!/bin/bash
# Description: command to generate ascii toy rnn data using python scripts from rakeshvar
# Usage: scribe.py <out_file_name> [alphabet=ascii] [avg_sequence_len=20] [noise=0.1] [variable_length=True]

output='data.pkl'
alphabet='ascii'
seqlen=22
noise=0.05

# python scribe.py data.pkl ascii
python scribe.py $output $alphabet $seqlen $noise