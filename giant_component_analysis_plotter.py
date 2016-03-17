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
    def giant_component_death_curve(calculate_on, pd_datas_1, windows_size, xlim=None, ylim=None):
        font = {'family': 'normal',
                'weight': 'normal',
                'size': 8}
        matplotlib.rc('font', **font)
        # plot the results
        fig = plt.figure(figsize=(9, 6))
        plot_gridspec = gridspec.GridSpec(3, 3, width_ratios=[1, 0.001, 1], height_ratios=[1, 0.001, 1])
        pd_datas = pd_datas_1
        graphs_index = 0
        ylabel = "Giant component size"
        ylabel = "Number of components"
        xlabel = "Normalized edge weight"
        markers = ['D', 's', '|', 'x', '_', '^', 'd', 'h', '+', '*', ',', 'o', '.', '1', 'p', '3', '2', '4', 'H', 'v', '8', '<', '>']
        markers = ['D', 's', 'x', '^', 'd', 'h', '+', '*', ',', 'o', '.', '1', 'p', '3', '2', '4', 'H', 'v', '8', '<', '>']
        x_lim = [numpy.inf, 0]
        y_lim = [numpy.inf, 0]
        for title in pd_datas:
            for title_legend in pd_datas[title]:
                x_lim[0] = min(x_lim[0], min(pd_datas[title][title_legend]['x']))
                x_lim[1] = max(x_lim[1], max(pd_datas[title][title_legend]['x']))
                y_lim[0] = min(y_lim[0], min(pd_datas[title][title_legend]['y']))
                y_lim[1] = max(y_lim[1], max(pd_datas[title][title_legend]['y']))
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
            if not xlim:
                plt.xlim(x_lim[0], x_lim[1])
            else:
                plt.xlim(*xlim)
            if not ylim:
                plt.ylim(y_lim[0], y_lim[1])
            else:
                plt.ylim(*ylim)
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
        # plt.savefig('/home/marcos/PhD/research/pso_influence_graph_communities/giant' +
        #             str(calculate_on) + '-' +
        #             '_'.join(map(str, windows_size)) + '.png', bbox_inches='tight')
        # plt.close()
        plt.show()

    @staticmethod
    def giant_component_death_curve_with_area(pd_datas, xlim=None, ylim=None, figsize=None, output_filename=None):
        font = {'family': 'normal',
                'weight': 'normal',
                'size': 10}
        matplotlib.rc('font', **font)
        # plot the results
        # fig = plt.figure(figsize=(9, 6))
        # plot_gridspec = gridspec.GridSpec(2, 2, width_ratios=[1, 0.001, 1], height_ratios=[1, 0.001, 1])
        if not figsize:
            figsize = (10, 2)
        f, axs = plt.subplots(1, len(pd_datas), sharey=True, figsize=figsize)
        graphs_index = 0
        ylabel = "Number of components"
        xlabel = "Normalized edge weight"
        markers = ['D', 's', '|', 'x', '_', '^', 'd', 'h', '+', '*', ',', 'o', '.', '1', 'p', '3', '2', '4', 'H', 'v', '8', '<', '>']
        markers = ['D', 's', 'x', '^', 'd', 'h', '+', '*', ',', 'o', '.', '1', 'p', '3', '2', '4', 'H', 'v', '8', '<', '>']
        markers = ['.', 'o']
        colors = ["#e41a1c", "#377eb8", "#fdae61", "#4daf4a"]
        x_lim = [numpy.inf, 0]
        y_lim = [numpy.inf, 0]
        legends = []
        for title in pd_datas:
            legends = pd_datas[title].keys()
            legends.sort()
            for title_legend in pd_datas[title]:
                x_lim[0] = min(x_lim[0], min(pd_datas[title][title_legend]['x']))
                x_lim[1] = max(x_lim[1], max(pd_datas[title][title_legend]['x']))
                y_lim[0] = min(y_lim[0], min(pd_datas[title][title_legend]['y']))
                y_lim[1] = max(y_lim[1], max(pd_datas[title][title_legend]['y']))
        axs[0].set_ylabel(ylabel)
        for title_legend in legends:
            ax = axs[graphs_index]
            # lines = ["-", "--", "-.", ":"]  # matplotlib.markers.MarkerStyle.markers.keys() #
            # markers = ["."]*len(lines) + ["v"]*len(lines) + ["^"]*len(lines)
            #
            # linecycler = cycle(lines)
            markercycler = cycle(markers)
            colorcycler = cycle(colors)
            hatch = cycle(['.', '|'])
            for title in pd_datas:
                color = next(colorcycler)
                curve = pd_datas[title][title_legend]
                pd_data = curve
                ax.grid(True)
                ax.plot(list(pd_data['x']) + [1.0], list(pd_data['y']) + [100],
                         # linestyle=next(linecycler),
                         marker=next(markercycler),
                         label=title, color=color,
                         markersize=4)
                ax.fill_between(list(pd_data['x']) + [1.0], 0.0, list(pd_data['y']) + [100.0], facecolor=color,
                                alpha=0.15, hatch=next(hatch))
            if not xlim:
                ax.set_xlim(x_lim[0], x_lim[1])
            else:
                ax.set_xlim(*xlim)
            if not ylim:
                ax.set_ylim(y_lim[0], y_lim[1])
            else:
                ax.set_ylim(*ylim)
            ax.set_title("$t_w=%d$" % title_legend)
            graphs_index += 1
        axs[1].legend(loc=4, numpoints=1)
        # plt.suptitle("Snapshot of the " + str(calculate_on) + "th iteration", fontsize=14)
        # plt.xlabel(xlabel, fontsize=12, labelpad=20)
        f.text(0.5, 0.03, xlabel, ha='center', va='center')
        plt.tight_layout()
        plt.subplots_adjust(0.09, 0.15)
        # ax3 = fig.add_subplot(plot_gridspec[1, 0])
        # ax3.set_yticks([])
        # ax3.set_xticks([])
        # ax3.set_frame_on(False)
        # plt.ylabel(ylabel, fontsize=12, labelpad=20)
        # ax3 = fig.add_subplot(plot_gridspec[2, 1])
        # ax3.set_yticks([])
        # ax3.set_xticks([])
        # ax3.set_frame_on(False)
        # plt.savefig('/home/marcos/PhD/research/pso_influence_graph_communities/giant' +
        #             str(calculate_on) + '-' +
        #             '_'.join(map(str, windows_size)) + '.png', bbox_inches='tight')
        # plt.close()
        if output_filename:
            plt.savefig(output_filename)
            #plt.clf()
            plt.close()
        else:
            plt.show()