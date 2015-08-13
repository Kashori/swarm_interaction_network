import math
import re
import igraph
import matplotlib
import sys
import numpy
import scipy
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from itertools import chain, cycle
from scipy.spatial.distance import pdist, squareform, euclidean
from scipy.cluster.hierarchy import dendrogram
from abc import abstractmethod, ABCMeta
from fastcluster import *
from matplotlib.lines import Line2D
import statsmodels.api as sm
import powerlaw


class Measure:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def calculate(self, matrix):
        pass


class Spectra(Measure):
    @staticmethod
    def calculate(self, matrix):
        #ev, = numpy.linalg.eig(matrix)
        return numpy.linalg.eig(matrix)


class SpectraUndirect(Measure):
    @staticmethod
    def calculate(self, matrix):
        #ev, = numpy.linalg.eig(matrix)
        size = len(matrix)
        for i in range(size):
            for j in range(size):
                if matrix[i][j] == matrix[j][i]:
                    continue
                if matrix[i][j] == 0 or matrix[j][i] == 0:
                    weight = max(matrix[i][j], matrix[j][i])
                    matrix[i][j] = weight
                    matrix[j][i] = weight
                else:
                    # the weights are different and nonzero, 
                    # many approaches can be used here: min,
                    # avg, max, etc. Let's do it 'max'. 
                    weight = max(matrix[i][j], matrix[j][i])
                    matrix[i][j] = weight
                    matrix[j][i] = weight
        teste = 0
        for i in range(size):
            for j in range(size):
                if matrix[i][j] != matrix[j][i]:
                    print "############################################################################## ERRR"
                    teste = 1
        if teste == 0:
            print "############################################################################## OK"
        print (str(matrix))
        return numpy.linalg.eig(matrix)


def to_symmetric(matrix):
    is_symmetric = numpy.triu(matrix) == numpy.transpose(numpy.tril(matrix))
    is_symmetric = is_symmetric.min()
    # here we sum
    if not is_symmetric:
        matrix = matrix + numpy.transpose(numpy.triu(matrix)) + numpy.transpose(numpy.tril(matrix))
    return matrix


class GiantComponentDeath:
    def __init__(self):
        pass

    @staticmethod
    def nodes_degree_removal(igraph_graph, graphs_keeper_giant_size_threshold=None, start_with_highest=True):
        #total_nodes = float(igraph_graph.vcount())
        graphs = []
        graphs_kept = []
        if graphs_keeper_giant_size_threshold:
            graphs_kept = list(set(graphs_keeper_giant_size_threshold))
            graphs_kept.sort(reverse=True)
            graphs_kept = map(lambda x: (False, x), graphs_kept)

        death_evolution_degree = []
        death_evolution_size = []
        graph_copy = igraph_graph.copy()
        removals = 0
        while graph_copy.vcount() > 0:
            removals += 1
            highest_degree = GiantComponentDeath.remove_nodes_with_highest_degree(graph_copy)
            total_nodes = float(graph_copy.vcount())
            print str(total_nodes)
            if total_nodes > 0:
                size_perc = graph_copy.components().giant().vcount()/total_nodes
            else:
                size_perc = 0
            death_evolution_size.append(size_perc)
            death_evolution_degree.append(removals)
            if graphs_keeper_giant_size_threshold:
                index_graph = 0
                for graph in graphs_kept:
                    if not graph[0]:
                        if graph[1] >= size_perc:
                            graphs.append((graph[1], size_perc, graph_copy.copy()))
                            graphs_kept[index_graph] = (True, graph[1])
                    index_graph += 1
        pd_df = pd.DataFrame({'x': death_evolution_degree, 'y': death_evolution_size})
        if graphs is not []:
            result = (pd_df, graphs)
        else:
            result = pd_df
        return result

    @staticmethod
    def low_edges_weight_removal(igraph_graph, graphs_keeper_giant_size_threshold=None):
        """ Removes the edges progressively by the weight starting with the ones with the lowest weight and returns
        the size of the giant component after each removal.

        :param igraph_graph:
        :param graphs_keeper_giant_size_threshold:
        :return:
        """
        total_nodes = float(igraph_graph.vcount())
        # it can keep graph structures for certain threhsolds, thus:
        graphs = []
        graphs_kept = []
        if graphs_keeper_giant_size_threshold:
            graphs_kept = list(set(graphs_keeper_giant_size_threshold))
            graphs_kept.sort(reverse=True)
            graphs_kept = map(lambda x: (False, x), graphs_kept)

        death_evolution_weight = []
        death_evolution_size = []
        number_of_components = []
        weight_values = list(set(igraph_graph.es['weight']))
        weight_values.append(0)
        weight_values.sort()
        graph_copy = igraph_graph.copy()
        for weight in weight_values:
            GiantComponentDeath.remove_weighted_edges(graph_copy, weight)
            death_evolution_weight.append(weight)
            size_perc = graph_copy.components().giant().vcount()/total_nodes
            death_evolution_size.append(size_perc)
            number_of_components.append(len(graph_copy.components()))
            ### this will keep the graphs
            if graphs_keeper_giant_size_threshold:
                index_graph = 0
                for graph in graphs_kept:
                    if not graph[0]:
                        if graph[1] >= size_perc:
                            graphs.append((graph[1], size_perc, graph_copy.copy()))
                            graphs_kept[index_graph] = (True, graph[1])
                    index_graph += 1
        # the result dataframe is sorted by the weight, low -> high
        #pd_df = pd.DataFrame({'x': death_evolution_weight, 'y': death_evolution_size})
        pd_df = pd.DataFrame({'x': death_evolution_weight, 'y': number_of_components})
        #print str(number_of_components)
        if graphs is not []:
            result = (pd_df, graphs)
        else:
            result = pd_df
        return result

    @staticmethod
    def remove_weighted_edges(igraph_graph, threshold=0.0):
        remove_them = []
        for e in igraph_graph.es:
            if e['weight'] <= threshold:
                remove_them.append(e.index)
        igraph_graph.delete_edges(remove_them)
        #return (remove_them)

    @staticmethod
    def remove_nodes_with_highest_degree(igraph_graph):
        highest_degree = max(igraph_graph.strength(weights='weight'))
        GiantComponentDeath.remove_nodes_with_degree(igraph_graph, highest_degree)
        return highest_degree

    @staticmethod
    def remove_nodes_with_degree(igraph_graph, degree):
        remove_them = []
        if 'weight' in igraph_graph.edge_attributes():
            degrees = igraph_graph.strength(weights='weight')
        else:
            degrees = igraph_graph.vs.degree()
        for v in igraph_graph.vs.indices:
            if degrees[v] == degree:
                remove_them.append(v)
        a = igraph_graph.vcount()
        igraph_graph.delete_vertices(remove_them)
        a -= igraph_graph.vcount()
        print 'removing all with degree ' + str(degree) + ' - removed ' + str(a)


def create_igraph_from_matrix(matrix, mode=igraph.ADJ_UNDIRECTED):
    if mode == igraph.ADJ_UNDIRECTED:
        # we are going to sum i,j to j,i:
        matrix = to_symmetric(matrix)
        # so, in the swarm, it means how many times a particle i and 
        # a particle j shared information (i->j and j->i are two information exchange) 
    g = igraph.Graph.Weighted_Adjacency(matrix.tolist())
    return g
    
        
class Parser:
    def __init__(self):
        pass

    @staticmethod
    def read_matrix_from_line(line, sep=' '):
        """ Reads a line a creates a square matrix.
        :param line: The string line.
        :param sep: The separator between the numbers. Default = ' '.
        :return: A numpy array.
        """
        matrix_result = None
        if line is not None and type(line) == str:
            matrix_read = line.strip().split(sep)
            matrix_read = list(map(float, matrix_read))
            number_of_elements = len(matrix_read)
            dimension_float = math.sqrt(number_of_elements) 
            dimension = math.trunc(dimension_float)
            if dimension == dimension_float:
                matrix_slices = [matrix_read[part:part+dimension] for part in range(0, number_of_elements, dimension)]
                matrix_result = numpy.array(matrix_slices)
            else:
                # this matrix cannot be assembled as a square matrix
                pass
            del matrix_read
        return matrix_result

    @staticmethod
    def read_vector_from_line(line, sep=' '):
        """ Reads a string and converts to a vector.
        :param line: The string line.
        :param sep: The separator between the numbers. Default = ' '.
        :return: A numpy array.
        """
        matrix_result = None
        if line is not None and type(line) == str:
            matrix_read = line.strip().split(sep)
            matrix_read = list(map(float, matrix_read))
            matrix_result = numpy.array(matrix_read)
        return matrix_result


def create_distance_matrix_from_positions(particle_positions, distance=euclidean):
    distance_matrix = None
    if particle_positions is not None:
        number_of_particles = len(particle_positions)
        distance_matrix = numpy.zeros((number_of_particles, number_of_particles))
        for i in particle_positions:
            for j in particle_positions:
                #todo: please, you should improve this...
                particle_distance = distance(particle_positions[i], particle_positions[j])
                distance_matrix[int(i)][int(j)] = particle_distance
    return distance_matrix


def remove_diagonal(array):
    array_result = array
    if array.shape[0] == array.shape[1]:
        array_reshaped = array.reshape((1, array.size))[0]
        diagonal_elements = range(0, array.size, array.shape[0]+1)
        array_removed = numpy.delete(array_reshaped, diagonal_elements)
        array_result = array_removed  # .reshape((array.shape[0]-1, array.shape[0]))
    return array_result


def calculate_correlation_influence_position(influence_graph, particles_positions):
    #todo: we may need to add the idea of transitivity, but we will need
    #todo: to explain why we do not take into account in the analyses
    distance_matrix = create_distance_matrix_from_positions(particles_positions)
    distance_matrix /= distance_matrix.max()
    distance_matrix = 1 - distance_matrix
    influence_graph /= influence_graph.max()
    #distance_reshaped = pd.Series(distance_matrix.reshape((1, distance_matrix.size))[0])
    #influence_reshaped = pd.Series(influence_graph.reshape((1, distance_matrix.size))[0])
    distance_reshaped = pd.Series(remove_diagonal(distance_matrix))
    influence_reshaped = pd.Series(remove_diagonal(influence_graph))
    correlation = distance_reshaped.corr(influence_reshaped)
    return correlation


def calculate_correlation_evolution(filename, iterations, windows_size, absolute_value=True, output_filename=None):
    pd_datas = []
    for iteration in iterations:
        correlation_evolution = []
        absolute_windows = []
        for window_size in windows_size:
            if type(window_size) is float:
                window_size = int(iteration * window_size)
            absolute_windows.append(window_size)
            ig, pos = EasyGraph.get_influence_graph_and_particles_position(filename, position_grep="position:#",
                                                                           influence_graph_grep="ig\:#[0-9]*",
                                                                           window_size=window_size,
                                                                           calculate_on=iteration)
            correlation = calculate_correlation_influence_position(ig, pos)
            correlation_evolution.append(correlation)
            print "iteration: " + str(iteration) + " with window: " + \
                  str(window_size) + " correlation: " + str(correlation)
        if absolute_value:
            pd_datas.append(pd.DataFrame({'x': absolute_windows, 'y': correlation_evolution}))
        else:
            pd_datas.append(pd.DataFrame({'x': windows_size, 'y': correlation_evolution}))
    Plotter.plot_curve(pd_datas,
                       output_filename=output_filename,
                       x_label="window size",
                       y_label="correlation with particle position",
                       legends=map(str, iterations))


def do_it():
    windows_size = [10, 100, 500, 1000]
    return read_files_and_plot([
        ('FSS1',
         '/home/marcos/PhD/research/pso_influence_graph_communities/fss_F6_original'),
        ('FSS2',
         '/home/marcos/PhD/research/pso_influence_graph_communities/fss_F6_original'),
        ('FSS3',
         '/home/marcos/PhD/research/pso_influence_graph_communities/fss_F6_original'),
        ('FSS4',
         '/home/marcos/PhD/research/pso_influence_graph_communities/fss_F6_original')],
        windows_size=-1,
        calculate_on=1000)

        # ('Ring',
        #  '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_ring_F6_13'),
        # ('Global',
        #  '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_global_F6_16'),
        # ('von Neumann',
        #  '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_neumann_F6_18')],
        # windows_size=-1,
        # calculate_on=1000)
    # return
    for calculate_on in range(100, 2501, 100):
        print str(calculate_on)
        read_files_and_plot(
            [
                ('Dynamic',
                 '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_dynamic_initial_ring_F6_16'),
                ('Ring',
                 '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_ring_F6_13'),
                ('Global',
                 '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_global_F6_16'),
                ('von Neumann',
                 '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_neumann_F6_18')],
            windows_size=-1,
            calculate_on=calculate_on)
    return
    windows_size = [10, 40, 50, 60, 70, 80, 90, 100]
    for iteration in range(100, 1501, 100):
        print str(iteration)
        read_files_and_plot([
            ('Dynamic',
             '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_dynamic_initial_ring_F6_16'),
            ('Ring',
             '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_ring_F6_13'),
            ('Global',
             '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_global_F6_16'),
            ('von Neumann',
             '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_neumann_F6_18')],
            windows_size,
            iteration)

    for iteration in range(500, 1501, 100):
        print str(iteration)
        windows_size = range(iteration - 4*100, iteration + 1, 100)
        read_files_and_plot([
            ('Dynamic',
             '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_dynamic_initial_ring_F6_16'),
            ('Ring',
             '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_ring_F6_13'),
            ('Global',
             '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_global_F6_16'),
            ('von Neumann',
             '/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_neumann_F6_18')],
            windows_size,
            iteration)


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
                '_'.join(map(str, windows_size)) + '.pdf', bbox_inches='tight')
    plt.close()


def create_giant_component_curves(all_graph_matrices, calculate_on, windows_size):
    pd_datas_1 = {}
    for title in all_graph_matrices:
        return_graphs_with_giant_sizes = [1.0, 0.9, 0.7, 0.5, 0.3]
        pd_datas_1[title] = {}
        for graph_matrix in all_graph_matrices[title]:
            title_legend, graph_matrix = graph_matrix
            #graph_matrix = to_symmetric(graph_matrix)
            igraph_graph = igraph.Graph.Weighted_Adjacency(graph_matrix.tolist(), mode=igraph.ADJ_MAX)
            # create the graph objects as well as the death analysis
            pd_data, graphs = GiantComponentDeath.low_edges_weight_removal(igraph_graph, return_graphs_with_giant_sizes)
            #pd_data, graphs = GiantComponentDeath.nodes_degree_removal(igraph_graph, return_graphs_with_giant_sizes)
            # normalize
            pd_data['x'] /= (2 * float(title_legend))
            pd_datas_1[title][title_legend] = pd_data

    # now we plot... pd_datas_1
    create_giant_component_death_curve(calculate_on, pd_datas_1, windows_size)


def create_strength_distribution_curves_windows_comparison(all_graph_matrices, calculate_on, windows_size):
    print str(all_graph_matrices)
    data_hists = {}
    for title in all_graph_matrices:
        for graph_matrix in all_graph_matrices[title]:
            title_legend, graph_matrix = graph_matrix
            # mode=igraph.ADJ_MAX, otherwise igraph sums up!
            igraph_graph = igraph.Graph.Weighted_Adjacency(graph_matrix.tolist(), mode=igraph.ADJ_MAX)
            # data_hists[title] = igraph_graph.degree()
            data_hist = igraph_graph.strength(weights='weight')
            if title_legend not in data_hists:
                data_hists[title_legend] = {}
            data_hists[title_legend][title] = data_hist
            #data_hists[title] = [w/float(calculate_on) for w in data_hists[title]]
            # and the weight distribution of it
            #all_edges_weights = list(chain(*igraph_graph.get_adjacency(attribute='weight')))
            #data_hists[title] = [w for w in all_edges_weights if w != 0.0]
    font = {'family': 'normal',
            'weight': 'normal',
            'size': 8}
    matplotlib.rc('font', **font)
    # plot the results
    fig = plt.figure(figsize=(9, 6))
    plot_gridspec = gridspec.GridSpec(3, 3, width_ratios=[1, 0.001, 1], height_ratios=[1, 0.001, 1])
    graphs_index = 0
    ylabel = r"$p(X\geq x)$"
    #ylabel = "Frequency"
    xlabel = "Node strength"
    ax3 = None
    lines = ["-", "--", ":", "-."]  # matplotlib.markers.MarkerStyle.markers.keys() #
    linecycler = cycle(lines)
    titles_sort = data_hists.keys()
    titles_sort.sort()
    titles_sort.reverse()
    for title in titles_sort:
        x = graphs_index / (len(data_hists) / 2)
        y = graphs_index % (len(data_hists) / 2)
        y = 2 if y == 1 else y
        x = 2 if x == 1 else x
        ax3 = fig.add_subplot(plot_gridspec[x, y])
        ax3.set_axisbelow(True)
        for title_legend in data_hists[title]:
            # plot with power law fit:
            fit = powerlaw.Fit(data_hists[title][title_legend], discrete=True)
            fit_fig = fit.plot_ccdf(label=title_legend, linestyle=next(linecycler),
                                    linewidth=1.6) #, marker='x', markersize=2)
            fit_fig.set_xscale("linear")
            fit_fig.set_yscale("linear")
        plt.tick_params(axis='both', which='major', labelsize=9)
        plt.tick_params(axis='both', which='minor', labelsize=9)
        plt.title("Window size = " + str(title))
        plt.grid(True)
        graphs_index += 1
    plt.legend(loc=1, fontsize=8)
    ax3 = fig.add_subplot(plot_gridspec[1, 0])
    ax3.set_yticks([])
    ax3.set_xticks([])
    ax3.set_frame_on(False)
    plt.ylabel(ylabel, fontsize=13, labelpad=20)
    ax3 = fig.add_subplot(plot_gridspec[2, 1])
    ax3.set_yticks([])
    ax3.set_xticks([])
    ax3.set_frame_on(False)
    plt.xlabel(xlabel, fontsize=13, labelpad=20)
    plt.suptitle("Snapshot of the " + str(calculate_on) +
                 "th iteration", fontsize=14)
    plt.savefig('/home/marcos/PhD/research/pso_influence_graph_communities/ccdf_comp' +
                str(calculate_on) + '-' +
                '_'.join(map(str, windows_size)) + '.pdf', bbox_inches='tight')
    plt.close()
    # plt.show()


def create_strength_distribution_curves(all_graph_matrices, calculate_on):
    data_hists = {}
    for title in all_graph_matrices:
        for graph_matrix in all_graph_matrices[title]:
            title_legend, graph_matrix = graph_matrix
            # mode=igraph.ADJ_MAX, otherwise igraph sums up!
            igraph_graph = igraph.Graph.Weighted_Adjacency(graph_matrix.tolist(), mode=igraph.ADJ_MAX)
            ####
            igraph.Graph.write_graphml(igraph_graph,
                                       '/home/marcos/PhD/research/pso_influence_graph_communities/' + title + "_"
                                       + str(title_legend) + "_" + str(calculate_on) + '.graphml')
            # data_hists[title] = igraph_graph.degree()
            data_hists[title] = igraph_graph.strength(weights='weight')
            #data_hists[title] = [w/float(calculate_on) for w in data_hists[title]]
            # and the weight distribution of it
            #all_edges_weights = list(chain(*igraph_graph.get_adjacency(attribute='weight')))
            #data_hists[title] = [w for w in all_edges_weights if w != 0.0]
    #return
    font = {'family': 'normal',
            'weight': 'normal',
            'size': 8}
    matplotlib.rc('font', **font)
    # plot the results
    fig = plt.figure(figsize=(9, 6))
    plot_gridspec = gridspec.GridSpec(3, 3, width_ratios=[1, 0.001, 1], height_ratios=[1, 0.001, 1])
    graphs_index = 0
    #ylabel = r"$p(X\geq x)$"
    ylabel = "Frequency"
    xlabel = "Node strength"
    xlim = [numpy.inf, 0]
    lines = ["-", "--", "-.", ":"]  # matplotlib.markers.MarkerStyle.markers.keys() #
    linecycler = cycle(lines)
    for title in data_hists:
        xlim[0] = min(xlim[0], min(data_hists[title]))
        xlim[1] = max(xlim[1], max(data_hists[title]))
    for title in data_hists:
        x = graphs_index / (len(data_hists) / 2)
        y = graphs_index % (len(data_hists) / 2)
        y = 2 if y == 1 else y
        x = 2 if x == 1 else x
        ax3 = fig.add_subplot(plot_gridspec[x, y])
        ax3.set_axisbelow(True)
        # plot with power law fit:
        fit = powerlaw.Fit(data_hists[title], discrete=True)
        fit_fig = fit.plot_ccdf(label='Empirical Data', marker='.') #linestyle=next(linecycler))
        fit_fig.set_xscale("linear")
        fit_fig.set_yscale("linear")

        # xvalues = numpy.linspace(min(data_hists[title]), max(data_hists[title]))
        # fit.power_law.plot_ccdf(ax=fit_fig, data=xvalues, color='r', linestyle='--', label='Power law fit')
        # print title
        # R, p = fit.distribution_compare('power_law', 'exponential', normalized_ratio=True)
        # if R < 0:
        #     print 'it is a power law with p = ' + str(p)
        # elif R > 0:
        #     print 'it is not a power law with p = ' + str(p)
        # else:
        #     print 'R = 0, p = ' + str (p)


        # ecdf = sm.distributions.ECDF(data_hists[title])
        # xvalues = numpy.linspace(min(data_hists[title]), max(data_hists[title]))
        # yvalues = 1 - ecdf(xvalues)
        # plt.scatter(xvalues, yvalues, c='blue', marker='.')
        # #plt.plot(xvalues, yvalues, c='blue', marker='.')
        # #plt.plot(ecdf.x, ecdf.y)
        # ax3.set_xscale("log")
        # ax3.set_yscale("log")


        #plt.xlim((xlim[0], xlim[1]))
        # plt.scatter(data_hists[title])
        # ax3.hist(data_hists[title],
        #          bins=15,
        #          facecolor='#758AB8',
        #          #edgecolor="none"
        #          #alpha=0.45
        #          )
        #plt.ylim(0, 12)
        plt.xlim(xlim[0], xlim[1])
        plt.tick_params(axis='both', which='major', labelsize=9)
        plt.tick_params(axis='both', which='minor', labelsize=9)
        plt.title(title)
        plt.grid(True)
        graphs_index += 1
    #plt.legend(loc=4)
    ax3 = fig.add_subplot(plot_gridspec[1, 0])
    ax3.set_yticks([])
    ax3.set_xticks([])
    ax3.set_frame_on(False)
    plt.ylabel(ylabel, fontsize=13, labelpad=20)
    ax3 = fig.add_subplot(plot_gridspec[2, 1])
    ax3.set_yticks([])
    ax3.set_xticks([])
    ax3.set_frame_on(False)
    plt.xlabel(xlabel, fontsize=13, labelpad=20)
    plt.suptitle("Snapshot of the " + str(calculate_on) +
                 "th iteration", fontsize=14)
    plt.savefig('/home/marcos/PhD/research/pso_influence_graph_communities/ccdf' +
                str(calculate_on) + '.pdf', bbox_inches='tight')
    plt.close()
    #plt.show()


def create_heatmap_plot(all_graph_matrices, calculate_on):
    heatmap_dfs = {}
    for title in all_graph_matrices:
        for graph_matrix in all_graph_matrices[title]:
            title_legend, graph_matrix = graph_matrix
            heatmap_dfs[title] = pd.DataFrame(graph_matrix)
    font = {'family': 'normal',
            'weight': 'normal',
            'size': 8}
    matplotlib.rc('font', **font)
    # plot the results
    fig = plt.figure(figsize=(9, 7))
    plot_gridspec = gridspec.GridSpec(3, 3, width_ratios=[1, 0.001, 1], height_ratios=[1, 0.001, 1])
    graphs_index = 0
    ylabel = "Particles"
    xlabel = "Particles"
    xlim = [numpy.inf, 0]
    for title in heatmap_dfs:
        x = graphs_index / (len(heatmap_dfs) / 2)
        y = graphs_index % (len(heatmap_dfs) / 2)
        y = 2 if y == 1 else y
        x = 2 if x == 1 else x
        ax3 = fig.add_subplot(plot_gridspec[x, y])
        ordered = True
        matrixdf = heatmap_dfs[title]
        ordered = False
        if ordered:
            row_pairwise_dists = squareform(pdist(matrixdf))
            row_clusters = linkage(row_pairwise_dists, method='complete')
            row_dendogram = dendrogram(row_clusters, no_plot=True, count_sort='ascending')

        # calculate pairwise distances for columns
        if ordered:
            col_pairwise_dists = squareform(pdist(matrixdf.T))
            col_clusters = linkage(col_pairwise_dists, method='complete')
            col_dendogram = dendrogram(col_clusters, no_plot=True, count_sort='ascending')
        axi = ax3.imshow(matrixdf, interpolation='nearest', aspect='auto', origin='lower')
        # axi = ax3.imshow(matrixdf.ix[row_dendogram['leaves'], col_dendogram['leaves']],
        # interpolation='nearest', aspect='auto', origin='lower')

        ax3.get_xaxis().set_ticks([])
        ax3.get_yaxis().set_ticks([])
        # fit.lognormal.plot_ccdf(ax=fit_fig, color='g', linestyle='--', label='Lognormal fit')
        # fit.exponential.plot_cdf(ax=fit_fig, color='y', linestyle='--', label='Exponencial fit')
        # fit.truncated_power_law.plot_cdf(ax=fit_fig, color='b', linestyle='--', label='Truncated fit')

        # return data_hists[title]
        # ecdf = sm.distributions.ECDF(data_hists[title])
        # xvalues = numpy.linspace(min(data_hists[title]), max(data_hists[title]))
        # yvalues = 1 - ecdf(xvalues)
        # plt.scatter(xvalues, yvalues, c='blue')
        #plt.xlim((10 ** 3, 10 ** 5))
        # plt.scatter(data_hists[title])
        # ax3.hist(data_hists[title],
        #          bins=100,
        #          facecolor='blue',
        #          alpha=0.45)
        # plt.tick_params(axis='both', which='major', labelsize=9)
        # plt.tick_params(axis='both', which='minor', labelsize=9)
        plt.title(title)
        graphs_index += 1
    plt.legend(loc=4)
    ax3 = fig.add_subplot(plot_gridspec[1, 0])
    ax3.set_yticks([])
    ax3.set_xticks([])
    ax3.set_frame_on(False)
    plt.ylabel(ylabel, fontsize=13, labelpad=20)
    ax3 = fig.add_subplot(plot_gridspec[2, 1])
    ax3.set_yticks([])
    ax3.set_xticks([])
    ax3.set_frame_on(False)
    plt.xlabel(xlabel, fontsize=13, labelpad=20)
    plt.suptitle("Snapshot of the " + str(calculate_on) +
                 "th iteration - Edges weight heatmap", fontsize=14)
    plt.savefig('/home/marcos/PhD/research/pso_influence_graph_communities/heatmap-' +
                str(calculate_on) + '.pdf', bbox_inches='tight')
    plt.close()


def read_files_and_plot(filenames, windows_size=None, calculate_on=None):
    # windows_size = [10, 40, 50, 60, 70, 80, 90, 100]
    # windows_size = [1, 5, 10, 15, 20] #, 40, 50, 60, 70, 80, 90, 100]
    # windows_size = [300, 400, 500]
    # calculates_on = [1300, 1400, 1500]
    # calculate_on = 1500
    fitness_grep = 'it\:#[0-9]*'
    influence_graph_grep = 'ig\:#[0-9]*'
    pre_callback = to_symmetric
    all_graph_matrices = {}
    for filename in filenames:
        title, filename = filename
        graph_matrices = []
        #for calculate_on in calculates_on:
        if type(windows_size) == int:
            windows_size = [windows_size]
        for window_size in windows_size:
            graph_index = window_size
            pos_callback = lambda x, y: graph_matrices.append((graph_index, x[1]))
            EasyGraph.read_file_and_measure(filename,
                                            calculate=None,
                                            influence_graph_grep=influence_graph_grep,
                                            fitness_grep=fitness_grep,
                                            window_size=window_size,
                                            pre_callback=pre_callback,
                                            pos_callback=pos_callback,
                                            calculate_on=calculate_on)
        all_graph_matrices[title] = graph_matrices
        ### create the GiantComponentDeath analysis
    create_giant_component_curves(all_graph_matrices, calculate_on, windows_size)
    #create_strength_distribution_curves_windows_comparison(all_graph_matrices, calculate_on, windows_size)
    #create_heatmap_plot(all_graph_matrices, calculate_on)
    #create_strength_distribution_curves(all_graph_matrices, calculate_on)

    # pd_data = (title, pd_data)
        # pd_datas_2.append(pd_data)

        # # but 'graphs' is actually igraph.graph, but we need
        # # networkx graphs, dammit! (because just nx.graph can be plot with matplotlib :( -- it seems)
        # nx_graphs = []
        # graph = None
        # for graph in graph_matrix:
        #     graph_component_histogram = graph[2].components().sizes()
        #     nx_graph = from_igraph_to_nxgraph(graph[2], only_connected_nodes=True)
        #     title = str(graph[1]) + " ("+str(graph[0])+") [" + str(nx.number_of_nodes(nx_graph)) \
        #                           + "/" + str(graph[2].vcount()) + "]"
        #     nx_graphs.append((title, nx_graph, graph_component_histogram))
        # if not nx_graphs:
        #     nx_graphs = None
        #
        # ### here is the fitness data
        # pd_data_1 = None
        # if fitness is not None:
        #     pd_data_1 = pd.DataFrame({'x': range(len(fitness)), 'y': fitness})
        #     pd_data_1 = ('Fitness', pd_data_1)

        ### create the histograms data
        # gets the last graph in 'graphs' and plot the degree distribution of it
  #return graph_matrix


class EasyGraph:
    def __init__(self):
        pass

    @staticmethod
    def get_influence_graph_and_particles_position(filename,
                                                   position_grep=None,
                                                   influence_graph_grep=None,
                                                   window_size=-1,
                                                   calculate_on=-1):
        """ Gets the influence graph and the particles positions in an iteration given.
        :param filename:
        :param position_grep:
        :param influence_graph_grep:
        :param window_size:
        :param calculate_on:
        :return:
        """
        input_file = open(filename, 'r')
        #window_size = 10
        windowed = window_size >= 1
        window = {}
        window_current = 0

        matrix_count = 0
        accumulated_matrix = None
        particles_position = {}
        ig_pp_return = None

        # let's get just the dimension of the influence graph
        for line in input_file:
            line, times = re.subn(influence_graph_grep, "", line)
            ig_greped = (times != 0)
            if ig_greped:
                accumulated_matrix = Parser.read_matrix_from_line(line)
                accumulated_matrix = numpy.zeros(accumulated_matrix.shape)
                break

        # rewind
        input_file.seek(0L)

        graph_done = False
        if accumulated_matrix is not None:
            for line in input_file:
                # tries to get influence graph
                line, times = re.subn(influence_graph_grep, "", line)
                ig_greped = (times != 0)
                if ig_greped and graph_done is False:
                    matrix_count += 1
                    matrix = Parser.read_matrix_from_line(line)
                    accumulated_matrix = accumulated_matrix + matrix
                    # let's keep the window history
                    if windowed:
                        window_current += 1
                        window[window_current % window_size] = matrix
                else:
                    # let's try to get a position vector,
                    # the pattern is something like: position:#0#i x y z
                    # what means that the position_grep = position:#
                    line, times = re.subn(position_grep, "", line)
                    pos_greped = (times != 0)
                    if pos_greped:
                        pos_match = re.match('^[0-9]*#[0-9]*', line)
                        if pos_match is not None:
                            pos_match = pos_match.group(0)
                            iteration, particle_id = pos_match.split('#')
                            if int(iteration) == calculate_on:
                                line_mod, _ = re.subn('^[0-9]*#[0-9]*', "", line)
                                particles_position[particle_id] = Parser.read_vector_from_line(line_mod)
                if matrix_count == calculate_on:
                    graph_done = True   # and we do not care about the graph anymore
                    if len(particles_position) != accumulated_matrix.shape[0]:
                        continue
                    if windowed:
                        graph_return = EasyGraph.sum_matrices(window)
                    else:
                        graph_return = accumulated_matrix
                    ig_pp_return = (graph_return, particles_position)
                    break
        input_file.close()
        return ig_pp_return

    @staticmethod
    def read_file_line_and_measure(filename, calculate, grep=None, pre_callback=None, pos_callback=sys.stdout.write):
        """ Reads each line in a file, creates a graph for each one based on the line content and measure the graph.
        :param filename: The filename of the file to be processed.
        :param calculate: The function used to measure the graph.
        :param grep: A regexp to use just specific lines of the file. The match is removed from the line.
        :param pre_callback: A function used to pre-process the graph.
        :param pos_callback: A function used to receive the mesasurement. If none, sys.stdout.write is used.
        :return: None.
        """
        input_file = open(filename, 'r')
        p = Parser()
        for line in input_file:
            if grep is not None:
                line, times = re.subn(grep, "", line)
                if times == 0:
                    continue 
            matrix = p.read_matrix_from_line(line)
            if pre_callback is not None:
                matrix = pre_callback(matrix)
                #print matrix
            matrix_measured = calculate(matrix)
            if pos_callback == sys.stdout.write:
                matrix_measured = str(matrix_measured) + "\n"
            pos_callback(matrix_measured)
        input_file.close()
    '''
     EasyGraph.read_file_and_measure(
     '/home/marcos/PhD/research/pso_influence_graph_communities/pso_dynamic_initial_ring_F6_30',
     SpectraUndirect.calculate, grep = 'ig\:#[0-9]*')
     EasyGraph.read_file_and_measure(
     '/home/marcos/PhD/research/pso_influence_graph_communities/pso_dynamic_initial_ring_F6_30',
     igraph.Graph.degree, grep = 'ig\:#[0-9]*', pre_callback = create_igraph_from_matrix)
    '''
    '''
    EasyGraph.read_file_and_measure_no_window(
    '/home/marcos/PhD/research/pso_influence_graph_communities/pso_dynamic_initial_ring_F6_30',
    igraph.Graph.degree, grep = 'ig\:#[0-9]*', pre_callback = create_igraph_from_matrix)
    EasyGraph.read_file_and_measure_no_window(
    '/home/marcos/PhD/research/pso_influence_graph_communities/50_particles/pso_dynamic_initial_ring_F6_30',
    calculate = None, grep = 'ig\:#[0-9]*', pre_callback = None, pos_callback = create_and_save_plot)
    '''
    @staticmethod
    def read_file_and_measure(filename,
                              calculate=None,
                              influence_graph_grep=None,
                              fitness_grep=None,
                              window_size=-1,
                              pre_callback=None,
                              pos_callback=sys.stdout.write,
                              calculate_on=-1):
        """ Measures each pair (fitnesses, graph) from the file.

        This function uses a regexp for fitness (or any other kind of information related to the graph) and a regexp
        for the graph. So, after finding a pair (fitness, graph), the graph is measured and this measurement is passed
        to the pos_callback function with the fitness values found so far. Thus, the pos_callback function must handle
        two arguments, where the first one is the result of the calculate function and the second one is a list of
        fitness values.

        :param filename:
        :param calculate:
        :param influence_graph_grep:
        :param fitness_grep:
        :param window_size:
        :param pre_callback:
        :param pos_callback:
        :return:
        """
        input_file = open(filename, 'r')
        #window_size = 10
        windowed = window_size >= 1
        window = {}
        window_current = 0

        # gets first line in order to create the sum_matrix
        matrix_count = 0
        fitnesses = None
        if fitness_grep:
            fitnesses = []
        ig_greped = False
        fitness_greped = False
        accumulated_matrix = None
        for line in input_file:
            ig_greped, fitness_greped, fitnesses, line = EasyGraph.grep_line(line, ig_greped, fitness_greped,
                                                                             fitnesses, influence_graph_grep,
                                                                             fitness_grep)
            # we will go until find ig and fitness
            if not ig_greped or (not fitness_greped and fitness_grep is not None):
                continue
            accumulated_matrix = Parser.read_matrix_from_line(line)
            matrix_count += 1
            sum_matrix_measured = accumulated_matrix
            # let's keep the window history
            if windowed:
                window[window_current % window_size] = sum_matrix_measured
                window_current += 1
                #print str(window)
                sum_matrix_measured = EasyGraph.sum_matrices(window)
            # does it calculate all the time? or only one shot?
            is_to_calculate = calculate == -1 or (calculate_on != -1 and matrix_count == calculate_on)
            # let's calculate
            if (matrix_count >= window_size or not windowed) and is_to_calculate:
                EasyGraph.measure(sum_matrix_measured, pre_callback, calculate,
                                  pos_callback, matrix_count, fitnesses)
            break

        # now we go to the other lines
        ig_greped = False
        fitness_greped = False
        # did we get the first line? did we already do what we needed?
        if accumulated_matrix is not None and not (calculate_on != -1 and matrix_count == calculate_on):
            for line in input_file:
                ig_greped, fitness_greped, fitnesses, line = EasyGraph.grep_line(line, ig_greped, fitness_greped,
                                                                                 fitnesses, influence_graph_grep,
                                                                                 fitness_grep)
                # we will go until find ig and fitness pair
                if not ig_greped or (not fitness_greped and fitness_grep is not None):
                    continue
                matrix_count += 1
                matrix = Parser.read_matrix_from_line(line)
                accumulated_matrix = accumulated_matrix + matrix
                sum_matrix_measured = accumulated_matrix
                ig_greped = False
                fitness_greped = False
                # let's keep the window history
                if windowed:
                    window_current += 1
                    window[window_current % window_size] = matrix
                    sum_matrix_measured = EasyGraph.sum_matrices(window)
                # does it calculate all the time? or only one shot?
                is_to_calculate = calculate == -1 or (calculate_on != -1 and matrix_count == calculate_on)
                # let's calculate
                if (matrix_count >= window_size or not windowed) and is_to_calculate:
                    EasyGraph.measure(sum_matrix_measured, pre_callback, calculate,
                                      pos_callback, matrix_count, fitnesses)
                # already done?
                if calculate_on != -1 and matrix_count >= calculate_on:
                    break
        input_file.close()

    @staticmethod
    def grep_line(line, ig_greped, fitness_greped, fitnesses, influence_graph_grep=None, fitness_grep=None):
        if influence_graph_grep is not None and not ig_greped:
            line, times = re.subn(influence_graph_grep, "", line)
            ig_greped = (times != 0)
        if fitness_grep is not None and not fitness_greped:
            fitness, times = re.subn(fitness_grep, "", line)
            fitness_greped = fitness_greped or (times != 0)
            if fitness_greped:
                #print str(fitness)
                fitnesses.append(float(fitness.strip()))
        return ig_greped, fitness_greped, fitnesses, line

    @staticmethod
    def measure(matrix, pre_callback, calculate, pos_callback, matrix_count, fitnesses=None):
        # matrix here can be symmetric or not, pre_callback should work on it...
        sum_matrix_measured = matrix
        if pre_callback is not None:
            sum_matrix_measured = pre_callback(matrix)
        if calculate is not None:
            sum_matrix_measured = calculate(sum_matrix_measured)
        # adds info about line read
        matrix_out = matrix_count, sum_matrix_measured
        ##
#             if (matrix_count == 100):
#                 return (sum_matrix_measured)
#             continue
        ##
        if pos_callback == sys.stdout.write:
            matrix_out = str(matrix_out).strip() + "\n"

        if pos_callback is not None:
            if fitnesses:
                pos_callback(matrix_out, fitnesses)
            else:
                pos_callback(matrix_out)

    @staticmethod
    def sum_matrices(window):
        """

        :rtype : object
        """
        sum_matrix = None
        if window is not None:
            sum_matrix = numpy.zeros(window[0].shape)
        for w in window:
            sum_matrix = sum_matrix + window[w]
        return sum_matrix


def str_and_print(obj):
    print (str(obj))
            

def from_igraph_to_nxgraph(igraph_graph, only_connected_nodes=False):
    nxgraph = nx.DiGraph()
    adjacency = list(igraph_graph.get_adjacency(attribute='weight'))
    if not only_connected_nodes:
        for i in range(len(adjacency)):
            nxgraph.add_node(i)
    for i in range(len(adjacency)):
        for j in range(len(adjacency)):
            if adjacency[i][j] != 0:
                nxgraph.add_edge(i, j, weight=adjacency[i][j])
    return nxgraph


def create_and_save_plot(matrix_out, fitness=None):
    ### FILENAME
    base_dir = '/home/marcos/PhD/research/pso_influence_graph_communities/50_particles/heatmaps/'
    if not ('append_filename' in globals()):
        append = ''
    else:
        # this is too dirty, but ok...
        global append_filename
        append = append_filename + '_'
    output_filename = base_dir+append+str(matrix_out[0])+'.png'
    print output_filename

    ### create the GiantComponentDeath analysis
    return_graphs_with_giant_sizes = [1.0, 0.9, 0.7, 0.5, 0.3]
    matrix = to_symmetric(matrix_out[1])
    igraph_graph = igraph.Graph.Weighted_Adjacency(matrix.tolist())

    # create the graph objects as well as the death analysis
    pd_data_2, graphs = GiantComponentDeath.low_edges_weight_removal(igraph_graph, return_graphs_with_giant_sizes)
    #pd_data_2, graphs = GiantComponentDeath.nodes_degree_removal(igraph_graph, return_graphs_with_giant_sizes)

    pd_data_2 = ('Giant Comp. Death', pd_data_2)

    # but 'graphs' is actually igraph.graph, but we need
    # networkx graphs, dammit! (because just nx.graph can be plot with matplotlib :( -- it seems)
    nx_graphs = []
    graph = None
    for graph in graphs:
        graph_component_histogram = graph[2].components().sizes()
        nx_graph = from_igraph_to_nxgraph(graph[2], only_connected_nodes=True)
        title = str(graph[1]) + " ("+str(graph[0])+") [" + str(nx.number_of_nodes(nx_graph)) \
                              + "/" + str(graph[2].vcount()) + "]"
        nx_graphs.append((title, nx_graph, graph_component_histogram))
    if not nx_graphs:
        nx_graphs = None

    ### here is the fitness data
    pd_data_1 = None
    if fitness is not None:
        pd_data_1 = pd.DataFrame({'x': range(len(fitness)), 'y': fitness})
        pd_data_1 = ('Fitness', pd_data_1)

    ### create the histograms data
    # gets the last graph in 'graphs' and plot the degree distribution of it
    data_hist_1 = ('Degree Distribution', graph[2].degree())
    all_edges_weights = list(chain(*graph[2].get_adjacency(attribute='weight')))
    # and the weight distribution of it
    data_hist_2 = ('Weight Distribution', [w for w in all_edges_weights if w != 0.0])
    Plotter.create_heatmap(matrix_out[1], main_title=str(matrix_out[0]),
                           output_filename=output_filename,
                           pd_data_1=pd_data_1,
                           pd_data_2=pd_data_2,
                           data_hist_1=data_hist_1,
                           data_hist_2=data_hist_2,
                           graphs=nx_graphs)


class Plotter:
    def __init__(self):
        pass

    @staticmethod
    def plot_curve(pd_data, title=None, x_label=None, y_label=None, output_filename=None, legends=None):
        if pd_data is not None:
            font = {'family': 'normal',
                    'weight': 'normal',
                    'size': 8}
            matplotlib.rc('font', **font)
            fig = plt.figure()
            #ax3 = fig.add_subplot(plot_gridspec[4, 2])
            if type(pd_data) is not list:
                plt.plot(pd_data['x'], pd_data['y'], linestyle='-', marker='.')
                plt.xlim(min(pd_data['x']), max(pd_data['x']))
            else:
                lines = ["-", "--", "-.", ":"]  # matplotlib.markers.MarkerStyle.markers.keys() #
                linecycler = cycle(lines)
                if legends:
                    legendcycler = cycle(legends)
                for pd_data_i in pd_data:
                    legend_title = None
                    if legends:
                        legend_title = cycle(legendcycler)
                    plt.plot(pd_data_i['x'], pd_data_i['y'], linestyle=next(linecycler),
                             marker='.', label=next(legend_title))
                    #plt.legend(loc=2)
                    plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
                plt.xlim(min(pd_data_i['x']), max(pd_data_i['x']))

            if x_label:
                plt.xlabel(x_label)
            if y_label:
                plt.ylabel(y_label)
            if title:
                plt.suptitle(title)
            if output_filename:
                plt.savefig(output_filename)
                #plt.clf()
                plt.close()
            else:
                plt.show()


    @staticmethod
    def create_heatmap(matrix,
                       main_title=None,
                       output_filename=None,
                       pd_data_1=None,
                       pd_data_2=None,
                       data_hist_1=None,
                       data_hist_2=None,
                       graphs=None,
                       ordered=False,
                       fitness_slice=500):
        matrixdf = pd.DataFrame(matrix)
        font = {'family': 'normal',
                'weight': 'normal',
                'size': 8}
        last_data_1 = 0.0
        matplotlib.rc('font', **font)
        # look at raw data
        #axi = plt.imshow(matrixdf,interpolation='nearest')
        #ax = axi.get_axes()
        
        #plt.clean_axis(ax)
        
        # row clusters
        if ordered:
            row_pairwise_dists = squareform(pdist(matrixdf))
            row_clusters = linkage(row_pairwise_dists, method='complete')
            row_dendogram = dendrogram(row_clusters, no_plot=True, count_sort='ascending')
    
        # calculate pairwise distances for columns
        if ordered:
            col_pairwise_dists = squareform(pdist(matrixdf.T))
            col_clusters = linkage(col_pairwise_dists, method='complete')
            col_dendogram = dendrogram(col_clusters, no_plot=True, count_sort='ascending')
            
        # plot the results
        fig = plt.figure(figsize=(12.5, 10))
        #plot_gridspec = gridspec.GridSpec(3,2, wspace=0.05,
        #  hspace=0.05, width_ratios=[0.25,1],height_ratios=[0.25,1,0.25])
        plot_gridspec = gridspec.GridSpec(5, 5, width_ratios=[0.15, 0.15, 0.2, 0.2, 0.2])
        
        ### col dendrogram ####
        #col_denAX = fig.add_subplot(plot_gridspec[0,1])
        if pd_data_1 is not None:
            title = ''
            if type(pd_data_1) == tuple:  # not so pythonic
                title = pd_data_1[0]
                pd_data_1 = pd_data_1[1]
            last_data_1 = pd_data_1['y'][len(pd_data_1)-1]
            
            #ax3 = fig.add_subplot(plot_gridspec[0,1])
            ax1 = plt.subplot(plot_gridspec[0, 2:])
            slice_base = max(0, len(pd_data_1) - fitness_slice)
            plt.plot(pd_data_1['x'], pd_data_1['y'], linestyle='-')
            plt.xlim(slice_base, len(pd_data_1))
            plt.title(title)
    #     else:
    #         col_denAX = fig.add_subplot(plot_gridspec[0,1])
        #create an empty graph

        ### row dendrogram ###
        #TODO: fix that please:
        if ordered:
            pass
            #row_denAX = fig.add_subplot(plot_gridspec[1,0])
            #row_denD = dendrogram(row_clusters, orientation='right', count_sort='ascending')
            #row_denAX.get_xaxis().set_ticks([]) # removes ticks
            
            #slice_base = max(0, max(pd_data_1['x']) - fitness_slice)
            #plt.plot(pd_data_1['x'], pd_data_1['y'], linestyle='-')
            #plt.xlim(slice_base, len(pd_data_1))

        if graphs is not None:
            gs_index = 0
            for title_graph in graphs:
                title, graph, graph_histogram = title_graph
                ax3 = plt.subplot(plot_gridspec[gs_index, 0])
                graph = graph.to_undirected()
                # we don't care about the weight because we already are filtering here
                nx.draw(graph, node_size=2, width=0.4, with_labels=False, 
                        pos=nx.spring_layout(graph, weight=None))
                plt.title(title)
                ax3 = plt.subplot(plot_gridspec[gs_index, 1])
                # let's add the histogram, but remove all 1 values
                graph_histogram_without_one = []
                for v in graph_histogram:
                    if v != 1:
                        graph_histogram_without_one.append(v)
                print str(graph_histogram_without_one)
#                 print str(graph_histogram)
                if not graph_histogram_without_one:
                    continue
                binwidth = 1
                min_bin = numpy.min(graph_histogram_without_one) 
                max_bin = numpy.max(graph_histogram_without_one)
                bins = range(min_bin, max_bin+binwidth, binwidth)
                ax3.hist(graph_histogram_without_one, bins=bins, facecolor='red', alpha=0.45)
                plt.xticks(numpy.unique(graph_histogram_without_one))
                plt.tick_params(axis='both', which='major', labelsize=5)
                plt.tick_params(axis='both', which='minor', labelsize=5)
#                plt.xticks(range(numpy.min(graph_histogram_without_one),
#                           numpy.max(graph_histogram_without_one),
#                           (numpy.min(graph_histogram_without_one) +  numpy.max(graph_histogram_without_one))/5))
                #plt.xlim(1, numpy.max(graph_histogram))
                if gs_index == 0:
                    plt.title("Components size\nhistogram")
                gs_index += 1
        
        ### heatmap ###
        heatmap_subplot = fig.add_subplot(plot_gridspec[1:4, 2:])
        
        if ordered:
            pass
            axi = heatmap_subplot.imshow(matrixdf.ix[row_dendogram['leaves'], col_dendogram['leaves']],
                                         interpolation='nearest', aspect='auto', origin='lower')
        else:
            axi = heatmap_subplot.imshow(matrixdf, interpolation='nearest', aspect='auto', origin='lower')
        # removes ticks
        heatmap_subplot.get_xaxis().set_ticks([])
        heatmap_subplot.get_yaxis().set_ticks([])
        axcolor = fig.add_axes([0.91, 0.27, 0.02, 0.45])
        plt.colorbar(axi, cax=axcolor)
        #fig.tight_layout()
        
        if pd_data_2 is not None:
            title = ''
            if type(pd_data_2) == tuple:  # not so pythonic
                title = pd_data_2[0]
                pd_data_2 = pd_data_2[1]
            ax3 = fig.add_subplot(plot_gridspec[4, 2])
            plt.plot(pd_data_2['x'], pd_data_2['y'], linestyle='-', marker='.')
            plt.xlim(min(pd_data_2['x']), max(pd_data_2['x']))
            #plt.ylim(0, 1.1)
            plt.title(title)
        
        if data_hist_1 is not None:
            title = ''
            if type(data_hist_1) == tuple:  # not so pythonic
                title = data_hist_1[0]
                data_hist_1 = data_hist_1[1]
            #binwidth = 1
            ax3 = fig.add_subplot(plot_gridspec[4, 3])
            #min_bin = numpy.min(data_hist_1)
            #max_bin = numpy.max(data_hist_1)
            #bins = range(min_bin,max_bin+binwidth,binwidth)
            ax3.hist(data_hist_1,  facecolor='blue', alpha=0.45)
            #plt.xticks(numpy.unique(data_hist_1))
            plt.tick_params(axis='both', which='major', labelsize=5)
            plt.tick_params(axis='both', which='minor', labelsize=5)
            plt.title(title)
            
        if data_hist_2 is not None:
            title = ''
            if type(data_hist_2) == tuple:  # not so pythonic
                title = data_hist_2[0]
                data_hist_2 = data_hist_2[1]
            if data_hist_2:
                ax3 = fig.add_subplot(plot_gridspec[4, 4])
                #bins = range(min_bin,max_bin+binwidth,binwidth)
                ax3.hist(data_hist_2,  facecolor='blue', alpha=0.45)
                #plt.xticks(numpy.unique(data_hist_1))
                plt.tick_params(axis='both', which='major', labelsize=5)
                plt.tick_params(axis='both', which='minor', labelsize=5)
                plt.title(title)
            
        if main_title:
            if pd_data_1 is not None:
                main_title = main_title + '\n(' + str(last_data_1).strip() + ')'
            plt.suptitle(main_title)
        if output_filename:
            plt.savefig(output_filename)
            #plt.clf()
            plt.close()
        else:
            plt.show()


'''
execfile('/home/marcos/pyworkspace/EasyGraph/EasyGraphpy')
append_filename = '
   without window:
   BADpso_dynamic_initial_ring_F6_16:it:#2999     2140695.499368374   OK sym
   GOODpso_dynamic_initial_ring_F6_02:it:#2999     21.318622649096547  OK sym and non-sym
   BADpso_ring_F6_13:it:#2999                     2372248.830220812   OK sym
   GOODpso_ring_F6_21:it:#2999                     1155170.4496039404  OK sym
   BADpso_global_F6_16:it:#2999                   4905393.756248348   OK sym
   GOODpso_global_F6_07:it:#2999                   1561303.7169722272  OK sym
   BADpso_static_neumann_04
   GOODpso_static_neumann_18
   BADpso_random_F6_07
   GOODpso_random_F6_12



execfile('/home/marcos/pyworkspace/EasyGraph/easygraph.py)
append_filename = 'pso_dynamic_ring_16_noW'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_dynamic_initial_ring_F6_16',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/EasyGraph/EasyGraphpy')
append_filename = 'pso_dynamic_ring_02_noW'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_dynamic_initial_ring_F6_02',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/EasyGraph/easygraph.py)
append_filename = 'pso_static_ring_13_noW'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_ring_F6_13',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/easy_graph/easygraph.py)
append_filename = 'pso_static_ring_21_noW'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_ring_F6_21',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/EasyGraph/easygraph.py)
append_filename = 'pso_static_global_16_noW'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_global_F6_16', calculate = None,
fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/EasyGraph/EasyGraphpy')
append_filename = 'pso_static_global_07_noW'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_global_F6_07',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/EasyGraph/easygraph.py)
append_filename = 'pso_static_neumann_18_w10'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_neumann_F6_18',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/EasyGraph/EasyGraphpy')
append_filename = 'pso_static_neumann_04_w10'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_neumann_F6_04',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/EasyGraph/EasyGraphpy')
append_filename = 'pso_random_F6_12_noW'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_random_F6_12',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)

execfile('/home/marcos/pyworkspace/EasyGraph/EasyGraphpy')
append_filename = 'pso_random_F6_07_noWs'
EasyGraph.read_file_and_measure(
'/home/marcos/PhD/research/pso_influence_graph_communities/100_particles/pso_random_F6_07',
calculate = None, fitness_grep = 'it\:#[0-9]*', influence_graph_grep = 'ig\:#[0-9]*',
pre_callback = to_symmetric, pos_callback = create_and_save_plot)
'''
