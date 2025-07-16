import numpy as np
import matplotlib.pyplot as plt
from scipy import misc
from PIL import Image

my_array = np.array([1.1, 9.2, 8.1, 4.7])

#show rows and columns
print(my_array.shape)
#accessing a particular index
print(my_array[2])
#show the dimensions of an array
print(my_array.ndim)

#two-dimensional array
array_2d = np.array([[1,2,3,9], [5,6,7,8]])

#verifying dimensions
print(f'array_2d has {array_2d.ndim} dimensions')
print(f'array_2d shape is {array_2d.shape}')
print(f'array_2d has {array_2d.shape[0]} rows and {array_2d.shape[1]} columns')
print(array_2d)
#print the entire first row
print(array_2d[0, :])
#access the 3rd value in the second row
print(array_2d[1,2])

#start and stop at a specific interval
a = np.arange(10,30)
print(a)

#grab the last 3 values of our created array
print(a[-3:])
#interval between 2 values
print(a[3:6])
#all of the values except the first 12
print(a[12:])
#every second value
print(a[::2])
#reverse the order
print(np.flip(a))
#get evenly spacesd numbers over an interval
print(np.linspace(a,2, num=1))

#broadcasting, scalars and matrix multiplication
#build your vectors
v1 = np.array([4, 5, 2, 7])
v2 = np.array([2, 1, 3, 3])

#build an narray
v1+v2
#multiplying the vectors to build an ndarray
v1*v2

#broadcasting
array_2d = np.array([[1, 2, 3, 4],
                     [5, 6, 7, 8]])
print(array_2d + 10)
print(array_2d * 5)

#matrix
a1 = np.array([[1, 3],
               [0, 1],
               [6, 2],
               [9, 7]])

b1 = np.array([[4, 1, 3],
               [5, 8, 5]])
c= np.matmul(a1,b1)
print(f'Matrix c has {c.shape[0]} rows and {c.shape[1]} columns.')

img = misc.face()
plt.imshow(img)
plt.show()
print(type(img))
print(img.shape)
print(img.ndim)

sRGB_array = img / 255
grey_vals = np.array([0.2126, 0.7152, 0.0722])
img_gray = sRGB_array @ grey_vals
img_gray = sRGB_array @ grey_vals
img_gray = np.matmul(sRGB_array, grey_vals)
#gray the image
plt.imshow(img_gray, cmap='gray')
plt.show()




