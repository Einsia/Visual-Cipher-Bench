"""Candidates print only the identity order and faces; tags are not compared."""
import numpy as np

def project(state):
    return {k: state[k] for k in ('order', 'faces')}

def matches(candidate, state):
    return candidate == project(state)

def matches_encoded(candidate, output):
    return np.array_equal(candidate['order'] + candidate['faces'], output[:6])
