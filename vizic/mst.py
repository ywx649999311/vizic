import numpy as np
from scipy.sparse.csgraph import minimum_spanning_tree as mst
from sklearn.neighbors import kneighbors_graph as kng
from scipy.sparse import find
from scipy.sparse.csgraph import connected_components as cp
from scipy.sparse import csr_matrix
import pandas as pd


def get_mst(df, neighbors):
    df = df[['RA', 'DEC']]
    numA = df.as_matrix(columns=['RA','DEC'])
    G = kng(numA,n_neighbors=neighbors,mode='distance')
    T = mst(G)
    index = find(T)
    row_ls = index[0].tolist()
    col_ls = index[1].tolist()
    df1 = df.ix[row_ls].reset_index()
    df2 = df.ix[col_ls].reset_index()
    df1 = df1.rename(columns={'RA':'RA1', 'DEC':'DEC1', 'index':'index1'})
    df2 = df2.rename(columns={'RA':'RA2', 'DEC':'DEC2', 'index':'index2'})
    final = pd.concat([df1,df2],axis=1)
    final['edges'] = pd.Series(index[2], index=final.index)
    final.reset_index(inplace=True)  # take index into columns for later filtering in JS
    final = final.rename(columns={'index':'line_index'})
    return final, index


def get_m_index(df):
    node_num = df.shape[0]+1
    index_mtx = csr_matrix((df['edges'].values,(df['index1'].values, df['index2'].values)), shape=(node_num, node_num))
    return find(index_mtx)


def cut_tree(mst_index, length, member):
    index = mst_index
    node_num = index[0].shape[0]+1
    lines = pd.DataFrame({'row':index[0], 'col':index[1], 'val':index[2]})

    cutted = lines[lines.val < length]  # get lines after cut
    # make csr matrix for finding connected components
    ccm = csr_matrix((cutted['val'].values,(cutted['row'].values, cutted['col'].values)),shape=(node_num, node_num))
    labels = cp(ccm, directed=False)[1]  # find connected components and get labels

    # sort out labels with small group members
    s = pd.Series(labels)
    df_s = s.reset_index(name='group')  # make label groups, make integer index one column and refer to node id
    gb = df_s.groupby('group')  # group by groups(labels)
    df_rt = gb.count()  # ordered by group labels, value is the counts, this is actually a dataframe
    label_cnts = df_rt['index']  # index is the column name
    label_cnts = label_cnts[label_cnts < member+1]  # find groups with less than n+1 node,
    # member is the provided min branch count

    rm_gps = label_cnts.index.values.tolist()  # groups with labels discarded
    node_ls = df_s[df_s.group.isin(rm_gps)]['index'].tolist()  # the list of nodes that will be discarded
    lines_rt = lines[(~lines.col.isin(node_ls))]  # remove line pairs that include node in node_ls
    saved_index = lines_rt.index.values.tolist()

    # return the wanted lines in the form of index
    return saved_index
