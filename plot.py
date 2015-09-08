from matplotlib.pylab import figure

fig = figure()
ax = fig.add_axes([.1, .1, .8, .8])
ax.plot([1,2,1.3,2,2.5])
fig.savefig('test.png')
