import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

fig, ax = plt.subplots()

OX = [ 'Ramprakash Radhakrishnan', 'Ajit Balagopal', 'Koushik Kannan', 'Deepa Seshadri', 'Abirambika', 'Balaji Vaidyanathan', 'Anupama R', 'Anupama Rajan',
       'Deepa Kumar', 'Akash Anandh', 'MLN', 'Bond', 'Swapna Nair' ]
OY = [ 100 * len(x) for x in OX ]
width = .35
ind = np.arange(len(OY))
rects = ax.bar(ind, OY)
#ax.set_xticks(ind + width / 2, OX)
ax.set_xticks(ind+width)
ax.set_xticklabels(OX)
ax.margins(0.05, 0.10)
plt.xticks(rotation=80)
#plt.subplots_adjust(left=0.05,right=0.10, top=0.10, bottom=0.0)

for rect in rects:
    height = rect.get_height()
    ax.text(rect.get_x()+rect.get_width()/2.0, height+10, '%d'%int(height),
            ha='center', va='bottom')

#fig.autofmt_xdate()
fig.tight_layout()
plt.savefig("figure.png")
