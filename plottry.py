import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, FixedFormatter, FuncFormatter
import StringIO

def bar_plot_names_messages(names, messages, ylabel, title, file_to_save, fmt):
    #fig = plt.figure(figsize=(1024, 768))
    #ax = fig.add_subplot(111)
    fig, ax = plt.subplots()
    #fig.figure()
    fig.set_size_inches(10.0, 7.5)

    width = .35
    ind = np.arange(len(messages))
    rects = ax.bar(ind, messages)
    #ax.set_xticks(ind + width / 2, names)
    ax.set_xticks(ind+width)
    texts = ax.set_xticklabels(names)
    for txt in texts:
        txt.set_horizontalalignment('right')
        txt.set_verticalalignment('top')
        txt.set_rotation_mode('anchor')
    ax.margins(0.05, 0.00)
    plt.xticks(rotation=30)
    #plt.subplots_adjust(left=0.05,right=0.10, top=0.10, bottom=0.0)

    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2.0, height+5, '%d'%int(height),
                ha='center', va='bottom')

    plt.ylim((0, max(messages) * 1.20))
    plt.title(title)
    #plt.xlabel('Smarts')
    plt.ylabel(ylabel)
    #fig.autofmt_xdate()
    fig.tight_layout()
    plt.savefig(file_to_save, format=fmt)

def line_plot_dates_messages(dates, messages, ylabel, title, file_to_save, fmt):
    #fig = plt.figure(figsize=(1024, 768))
    #ax = fig.add_subplot(111)
    fig, ax = plt.subplots()
    #fig.figure()
    fig.set_size_inches(10.0, 7.5)

    width = .35
    ind = np.arange(len(messages))
    lines = ax.plot(ind, messages)
    #ax.set_xticks(ind + width / 2, dates)
    ax.set_xticks(ind)
    texts = ax.set_xticklabels(dates)
    for txt in texts:
        txt.set_horizontalalignment('right')
        txt.set_verticalalignment('top')
        txt.set_rotation_mode('anchor')
    ax.margins(0.05, 0.00)
    plt.xticks(rotation=30)
    #plt.subplots_adjust(left=0.05,right=0.10, top=0.10, bottom=0.0)

    #for rect in rects:
    #    height = rect.get_height()
    #    ax.text(rect.get_x()+rect.get_width()/2.0, height+5, '%d'%int(height),
    #            ha='center', va='bottom')
    for i, ix in enumerate(ind):
        xy = (ix, messages[i])
        xytext = (ix, messages[i]+10)
        ax.annotate(str(messages[i]), xy, xytext)
        
    plt.ylim((0, max(messages) * 1.20))
    plt.title(title)
    #plt.xlabel('Smarts')
    plt.ylabel(ylabel)
    #fig.autofmt_xdate()
    fig.tight_layout()
    plt.savefig(file_to_save, format=fmt)

def fill_plot_ticks_messages(xtick_labels, messages, ylabel, title, file_to_save, fmt):
    #fig = plt.figure(figsize=(1024, 768))
    #ax = fig.add_subplot(111)
    fig, ax = plt.subplots()
    #fig.figure()
    fig.set_size_inches(10.0, 7.5)

    width = .35
    ind = np.arange(len(messages))
    lines = ax.plot(ind, messages, color='blue')
    ax.fill_between(ind, 0, messages, facecolor='blue')
    #ax.set_xticks(ind + width / 2, dates)
    
    #ax.set_xticks(np.arange(len(xtick_labels)))
    #texts = ax.set_xticklabels(xtick_labels)
    #for txt in texts:
    #    txt.set_horizontalalignment('right')
    #    txt.set_verticalalignment('top')
    #    txt.set_rotation_mode('anchor')
    
    def get_xtick_label(x, pos):
        i = x/mul
    
    mul = len(messages)/len(xtick_labels)
    print 'Mul=', mul
    def get_xtick_label(x, pos):
        i = int(x/mul)
        #print 'Get xtick label: x, pos, i = ', x, pos, i
        if i < 0 or i >= len(xtick_labels):
            return ''
        return xtick_labels[i]
        
    majorLocator   = MultipleLocator(mul)
    majorFormatter = FuncFormatter(get_xtick_label)#FixedFormatter(xtick_labels)#FormatStrFormatter('%d')
    #minorLocator   = MultipleLocator(1)
    
    ax.xaxis.set_major_locator(majorLocator)
    ax.xaxis.set_major_formatter(majorFormatter)

    #for the minor ticks, use no labels; default NullFormatter
    #ax.xaxis.set_minor_locator(minorLocator)

    ax.margins(0.05, 0.00)
    plt.xticks(rotation=30)
    #plt.subplots_adjust(left=0.05,right=0.10, top=0.10, bottom=0.0)

    #for rect in rects:
    #    height = rect.get_height()
    #    ax.text(rect.get_x()+rect.get_width()/2.0, height+5, '%d'%int(height),
    #            ha='center', va='bottom')
    #for i, ix in enumerate(ind):
    #    xy = (ix, messages[i])
    #    xytext = (ix, messages[i]+10)
    #    ax.annotate(str(messages[i]), xy, xytext)
        
    plt.ylim((0, max(messages) * 1.20))
    plt.title(title)
    #plt.xlabel('Smarts')
    plt.ylabel(ylabel)
    #fig.autofmt_xdate()
    fig.tight_layout()
    plt.savefig(file_to_save, format=fmt)


if __name__=='__main__':
    OX = [ 'Ramprakash Radhakrishnan', 'Ajit Balagopal', 'Koushik Kannan', 'Deepa Seshadri', 'Abirambika', 'Balaji Vaidyanathan', 'Anupama R', 'Anupama Rajan',
           'Deepa Kumar', 'Akash Anandh', 'MLN', 'Bond', 'Swapna Nair' ]
    OX.sort()       
    OY = [ 100 * len(x) for x in OX ]
    print OY
    bar_plot_names_messages(OX, OY, 'No. of messages', 'Messages per head today', "figure_names.png", "png")
    line_plot_dates_messages(OX, OY, 'No. of messages', 'Messages per head today', "figure_dates.png", "png")
    
    time_tick_labels = ['Midnight', '3 am', '6 am', '9 am', '12 noon', '3 pm', '6 pm', '9 pm']
    fill_OY = [1] * (24 * 60)
    fill_plot_ticks_messages(time_tick_labels, fill_OY, 'No. of messages', 'Messages per head today (xticks unrelated)', "fill_plot_figure.png", "png")

