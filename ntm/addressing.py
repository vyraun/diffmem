"""
This module implements addressing as described in the paper.
It's basically a python version of figure 2.
"""
import autograd.numpy as np

def cosine_sim(a_t, b_t):
    """
    Computes the cosine similarity of vectors a and b.
    Specifically \frac{u \cdot v}{||u|| \cdot ||v||}.
    """
    # numerator is the inner product
    num = np.dot(a_t, b_t)

    # denominator is the product of the norms
    anorm = np.sqrt(np.sum(a_t*a_t))
    bnorm = np.sqrt(np.sum(b_t*b_t))
    den2 = (anorm * bnorm) + 1e-20

    return num / den2

def content_focus(k_t, b_t, mem):
    """
    The content-addressing method described in 3.3.1.
    Specifically, this is equations (5) and (6).
    k_t is the similarity key vector.
    b_t is the similarity key strength.
    memObject is a ref to our NTM memory object.
    """
    def K(u):
        """
        Given the key vector k_t, compute our sim
        function between k_t and u and exponentiate.
        """
        return np.exp(b_t * cosine_sim(u, k_t))

    # Apply above function to every row in the matrix
    # This is surely much slower than it needs to be
    l = []
    for row in mem:
        l.append(K(row)[0])

    # Return the normalized similarity weights
    # This is essentially a softmax over the similarities
        # with an extra degree of freedom parametrized by b_t
    sims = np.array(l)

    n = sims
    d = np.sum(sims)
    return n/d

def shift(w_gt, s_t):
    """
    Perform the shifting operation as described in equation 8 from the paper.
    """

    # This function could be more performant.
    N = w_gt.size

    backward = [1, 0, 0]
    same     = [0, 1, 0]
    forward  = [0, 0, 1]
    null     = [0, 0, 0]

    restrictionList = []
    for i in range(0, N):
        if i == 0:
            restrictionList.append(backward)
        elif i == 1:
            restrictionList.append(same)
        elif i == N-1:
            restrictionList.append(forward)
        else:
            restrictionList.append(null)

    rT = np.array(restrictionList)

    if N >= 3:
        s_t = np.dot(rT, s_t)

    sums = []
    for i in range(N):
        sums.append(0)
        for j in range(N):
            sums[i] += w_gt[j] * s_t[(i - j) % N]

    return np.array(sums)

def location_focus(g_t, s_t, gamma_t, w_old, w_content):
    """
    The location-addressing method described in 3.3.2.
    Specifically, this is equations (7), (8), and (9).
    g_t is the interpolation gate and it lies in (0,1).
    s_t is the shift weight vector:
        The shift weight vector is of length V, where V is the number
        of allowed integer shifts. e.g. if we allow shifts 0,1, and -1
        (which are computed modulo N and so can be though of as 0,1,2)
        then our shift vector lies in R^3, has non-negative entries,
        and sums to 1. If you wanted to encode a matrix down-shift of 1 row,
        you would pass [0,1,0] here. [1,0,0] corresponds to no shift.
    gamma_t \geq 1 is is sharpening scalar.
    w_old is the weight used by this head for the last time step.
    w_content is the weight generated by the content addressing mechanism
        at the current time step, t.
    """
    # Use the interpolation gate to smooth between old and new weights.
    w_gt = g_t * w_content + (1-g_t) * w_old

    # convolve w_gt with s_t to get shifted weights
    # w_tp = shift(w_gt, s_t)

    # Take every element of the weight vector to the gamma_t-th power.
    # pows = w_tp ** gamma_t

    # Normalize that vector by its sum.
    # w_t = pows / np.sum(pows)

    # return w_t
    return w_gt

def create_weights(k_t, b_t, g_t, s_t, gamma_t, w_old, mem):
    """
    Convenience function to be called from NTM fprop.
    """
    w_content = content_focus(k_t, b_t, mem)
    return location_focus(g_t, s_t, gamma_t, w_old, w_content), w_content
