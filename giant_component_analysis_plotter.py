__author__ = 'marcos'
import matplotlib
import numpy
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from itertools import cycle


class GiantComponentDeathPlotter:
    def __init__(self):
        pass

    @staticmethod
    def create_giant_component_death_curve(calculate_on, pd_datas_1, windows_size):
        font = {'family': 'normal',
                'weight': 'normal',
                'size': 8}
        matplotlib.rc('font', **font)
        # plot the results
        fig = plt.figure(figsize=(9, 6))
        plot_gridspec = gridspec.GridSpec(3, 3, width_ratios=[1, 0.001, 1], height_ratios=[1, 0.001, 1])
        pd_datas = pd_datas_1
        graphs_index = 0
        xlim = [numpy.inf, 0]
        ylim = [numpy.inf, 0]
        ylabel = "Giant component size"
        ylabel = "Number of components"
        xlabel = "Normalized edge weight"
        markers = ['D', 's', '|', 'x', '_', '^', 'd', 'h', '+', '*', ',', 'o', '.', '1', 'p', '3', '2', '4', 'H', 'v', '8', '<', '>']
        markers = ['D', 's', 'x', '^', 'd', 'h', '+', '*', ',', 'o', '.', '1', 'p', '3', '2', '4', 'H', 'v', '8', '<', '>']
        for title in pd_datas:
            for title_legend in pd_datas[title]:
                xlim[0] = min(xlim[0], min(pd_datas[title][title_legend]['x']))
                xlim[1] = max(xlim[1], max(pd_datas[title][title_legend]['x']))
                ylim[0] = min(ylim[0], min(pd_datas[title][title_legend]['y']))
                ylim[1] = max(ylim[1], max(pd_datas[title][title_legend]['y']))
        for title in pd_datas:
            x = graphs_index / (len(pd_datas) / 2)
            y = graphs_index % (len(pd_datas) / 2)
            y = 2 if y == 1 else y
            x = 2 if x == 1 else x
            #ax3 = fig.add_subplot(plot_gridspec[x, y])
            ax = fig.add_subplot(plot_gridspec[x, y])
            ax.set_axisbelow(True)
            legends = pd_datas[title].keys()
            legends.sort()
            # lines = ["-", "--", "-.", ":"]  # matplotlib.markers.MarkerStyle.markers.keys() #
            # markers = ["."]*len(lines) + ["v"]*len(lines) + ["^"]*len(lines)
            #
            # linecycler = cycle(lines)
            markercycler = cycle(markers)
            for title_legend in legends:
                curve = pd_datas[title][title_legend]
                pd_data = curve
                plt.grid(True)
                plt.plot(pd_data['x'], pd_data['y'],
                         # linestyle=next(linecycler),
                         marker=next(markercycler),
                         label=title_legend,
                         markersize=4)
            plt.ylim(ylim[0], ylim[1])
            plt.xlim(xlim[0], xlim[1])
            plt.title(title)
            graphs_index += 1
        plt.legend(loc=4)
        ax3 = fig.add_subplot(plot_gridspec[1, 0])
        ax3.set_yticks([])
        ax3.set_xticks([])
        ax3.set_frame_on(False)
        plt.ylabel(ylabel, fontsize=12, labelpad=20)
        ax3 = fig.add_subplot(plot_gridspec[2, 1])
        ax3.set_yticks([])
        ax3.set_xticks([])
        ax3.set_frame_on(False)

        plt.xlabel(xlabel, fontsize=12, labelpad=20)
        plt.suptitle("Snapshot of the " + str(calculate_on) + "th iteration", fontsize=14)
        plt.savefig('/home/marcos/PhD/research/pso_influence_graph_communities/giant' +
                    str(calculate_on) + '-' +
                    '_'.join(map(str, windows_size)) + '.png', bbox_inches='tight')
        plt.close()