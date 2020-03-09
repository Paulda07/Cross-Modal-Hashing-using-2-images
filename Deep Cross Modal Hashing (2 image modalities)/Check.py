"""
import  numpy as np
a = np.array([[1,2],[3,4]]) 
b = np.array([[11,12],[13,14]]) 
print(np.dot(a,b))
"""
import  numpy as np
gnd=[0.0, 1.0, 1.0, 0.0, 0.0, 0.0]
tindex = np.asarray(np.where(gnd == 1)) + 1.0
print(tindex)