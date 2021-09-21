from scipy.interpolate import interp1d, Akima1DInterpolator
import numpy as np
import matplotlib.pyplot as plt

x = np.array([0.01, 0.1, 0.15, 0.85, 0.9, 1])
y = np.array([0,    1,   1,    1,    1,   0])
plt.plot(x,y, marker="o", ls="")

sx=np.log10(x)
xi_ = np.linspace(sx.min(),sx.max(), num=201)
xi = 10**(xi_)

print(Akima1DInterpolator(sx, y)(0.1))

f2 = Akima1DInterpolator(sx, y)
yi2 = f2(xi_)
plt.plot(xi,yi2, label="Akima")

plt.gca().set_xscale("log")
plt.legend()
plt.show()