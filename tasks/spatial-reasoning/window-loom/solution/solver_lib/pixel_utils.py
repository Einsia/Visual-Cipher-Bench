import math
import numpy as np


def components(mask):
    parents, runs, previous = [], [], []

    def find(k):
        while parents[k] != k:
            parents[k] = parents[parents[k]]
            k = parents[k]
        return k

    for y, row in enumerate(mask):
        edges = np.flatnonzero(np.diff(np.pad(row.astype(np.int8), (1, 1))))
        current, j = [], 0
        for left, right in zip(edges[::2], edges[1::2]):
            k = len(parents)
            parents.append(k)
            runs.append((int(left), y, int(right), k))
            current.append((left, right, k))
            while j < len(previous) and previous[j][1] < left:
                j += 1
            t = j
            while t < len(previous) and previous[t][0] <= right:
                parents[find(k)] = find(previous[t][2])
                t += 1
        previous = current
    result = {}
    for left, y, right, k in runs:
        k = find(k)
        if k not in result:
            result[k] = {'box': [left, y, right, y+1], 'area': 0, 'runs': []}
        obj = result[k]
        b = obj['box']
        b[0], b[1] = min(b[0], left), min(b[1], y)
        b[2], b[3] = max(b[2], right), max(b[3], y+1)
        obj['area'] += right-left
        obj['runs'].append([left, y, right])
    return list(result.values())

def rgb_mask(arr, color, tolerance=16):
    return np.max(np.abs(arr.astype(np.int16)-np.array(color)), axis=-1) < tolerance

def rod(axis, degrees):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    skew = np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    theta = math.radians(degrees)
    return (np.eye(3)*math.cos(theta) + (1-math.cos(theta))*np.outer(axis,axis)
            + math.sin(theta)*skew)
