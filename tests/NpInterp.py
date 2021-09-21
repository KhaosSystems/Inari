import numpy as np
import matplotlib.pyplot as plt


x = np.array([])
y = np.array([])

for i in range(0, 100):
    x = np.append(x, i)
    firstFloat = 0
    secondFloat = 1
    alpha = max(0, min(i/10, 1)) +  max(0.9, min(i-i/10, 2))
    y = np.append(y, alpha)

print(y)


plt.plot(x, y, marker="o", ls="")
plt.show()