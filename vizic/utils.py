import healpy as hp
import numpy as np
import pandas as pd
from scipy.sparse.csgraph import minimum_spanning_tree as mst
from sklearn.neighbors import kneighbors_graph as kng
from scipy.sparse import find
from scipy.sparse.csgraph import connected_components as cp
from scipy.sparse import csr_matrix


def get_mst(df, neighbors):
    """Compute the Minimum Spanning Tree (MST) from postions.

    This function takes a pandas dataframe of poistions and compute the distances to k-neighbors for all poistions given, then find the MST using ``scipy.sparse.csgraph``. Finally finds the non-zero elements in a returned sparse matrix.

    Args:
        df: A pandas dataframe all positions with longitude as ``RA`` and
            latitute as ``DEC``.
        neighbors(int): The number of neighbors used when computing tress.

    Returns:
        A pandas dataframe for all edges in the MST and a tuple of arrays storing the indexes and values of non-zero elements in the MST sparse matrix.
    """
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
    """Find the index from a given dataframe of MST edges.

    Args:
        df: A pandas dataframe of MST edges.

    Returns:
        A tuple of arrays storing the indexes and values of non-zero elements in the MST sparse matrix.
    """
    node_num = df.shape[0]+1
    index_mtx = csr_matrix((df['edges'].values,(df['index1'].values, df['index2'].values)), shape=(node_num, node_num))
    return find(index_mtx)


def cut_tree(mst_index, length, member):
    """Find the index for saved edges after a cut.

    Note:
        At the frond-end all edges in a MST are stored in a JavaScript array and this function only returns the indexes for wanted edges.

    Args:
        mst_index: A tuple of arrays indicating the indexes and values for the
            MST sparse matrix.
        length(float): The maximum length for edges in a trimmed tree. All edges
            above are cutted off.
        member(int): Minimum number of edges required in a saved branch. All
            branches having less members are removed in the final tree.

    Returns:
        A list of integers representing the index for saved edges.
    """
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


# Functions for Healpix
def get_vert(pixel, nside, nest):
    """Get the coordinates for the vertices for a single Healpix index for a given
    resolution (nside) and schema (nest)

    Args:
        * All arguments are required
        pixel(int): Healpix index
        nside(int) : Healpix resolution given by nside parameters for the input pixel
        nest(bool): Pixelization schema, True: Nested Schema, False: Ring Schema
    Returns:
        Two lists with the RA and DEC positions for the vertices for the given pixel.
    """
    # Get vertices in radian coordinates for a given pixel
    vertices = np.array(hp.vec2ang(np.transpose(hp.boundaries(nside,pixel,nest=nest))))
    # To degrees
    vertices = vertices*180./np.pi
    diff = vertices[1] - vertices[1][0]  # RA = 0
    diff[diff > 180] -= 360
    diff[diff < -180] += 360
    ra_vert = vertices[1][0] + diff
    ra_vert = np.append(ra_vert,ra_vert[0])
    dec_vert = 90.0 - vertices[0]
    dec_vert = np.append(dec_vert,dec_vert[0])
    return ra_vert,dec_vert


def is_inside_bbox(ra,dec,llra,lldec,urra,urdec):
    """Find whether a point is inside a bounding box.

    Args:
        ra(float): Right ascension of the query point.
        dec(float): Declination of the query point.
        llra(float): Lower left RA for the bounding box.
        lldec(float): Lower left DEC for the bounding box.
        urra(float): Upper right RA for the bounding box.
        urdec(float): Upper right DEC for the bounding box.

    Returns:
        A Bool whether the point is inside the bounding box.

    TODO: Use ray tracing for any polygon shape
    """
    if (ra <= urra) & (ra >= llra) & (dec <= urdec) & (dec >= lldec):
        return True
    else:
        return False


def get_vert_bbox(llra,lldec,urra,urdec,nside,nest):
    """Get a list of the vertices for all Healpix pixels inside a given bounding
    box, resolution and pixelization schema.

    Args:
        llra(float): Lower left RA for the bounding box.
        lldec(float): Lower left DEC for the bounding box.
        urra(float): Upper right RA for the bounding box.
        urdec(float): Upper right DEC for the bounding box.
        nside(int) : Healpix resolution given by nside.
        nest(bool): Pixelization schema, True: Nested Schema, False: Ring Schema

    Returns:
        A list with the vertices for all pixels inside the bounding box.
    """
    # Find central point for the bbox
    mid_ra = (urra+llra)/2.
    mid_dec = (urdec + lldec)/2.
    # Convert to radians
    phi = mid_ra/180.*np.pi
    th = (90.-mid_dec)/180.*np.pi
    pix = hp.ang2pix(nside,th,phi,nest)  # Pixel at center
    neig = hp.get_all_neighbours(nside,pix,None,nest)  # Get initial 8 neighbors
    # Create a set
    allp = set(neig)
    checked_big = set()
    checked_all = set()
    k = 0
    # Find all pixels inside bounding box by looking at all the neighbors'
    # neighbors recursively using a set to speed up the process.
    while True:
        if k == 10000:
            raise RuntimeError('Did not converge, increase k limit')
        # Create a copy of the intial set of neighbors
        temp = allp.copy()
        for i in temp.copy().difference(checked_big):
            ntemp = set(hp.get_all_neighbours(nside,i,None,nest))
            for j in ntemp.difference(checked_all):
                th2,phi2 = hp.pix2ang(nside,j,nest)
                # Check if given neighbor is inside the bbox
                if is_inside_bbox(phi2*180./np.pi,90-th2*180./np.pi,llra,lldec,urra,urdec):
                    temp.add(j)
            # Update set to keep track of checked pixels
            checked_all.update(ntemp)
            checked_big.add(i)
        if temp == allp:
            break
        else:
            allp.update(temp)
            k += 1
    all_verts = []
    # Get vertices for pixels inside bounding box
    for i in allp:
        all_verts.append(get_vert(i, nside,nest))
    # Return complete list
    return all_verts
