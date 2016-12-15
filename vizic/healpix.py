import healpy as hp
# import matplotlib.pyplot as plt
import numpy as np
# NEST = True  # Keep it true
# NSIDE = 1024  # must be a power of 2


def get_vert(pixel, nside, nest):
    vertices = np.array(hp.vec2ang(np.transpose(hp.boundaries(nside,pixel,nest=nest))))
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
    # for a simple box for now, ray tracing for any polygon TBD
    # llra: lower left ra
    # lldec: lower left dec
    # urra: upper right ra
    # urdec: upper right dec
    if (ra <= urra) & (ra >= llra) & (dec <= urdec) & (dec >= lldec):
        return True
    else:
        return False


def get_vert_bbox(llra,lldec,urra,urdec,nside,nest):
    # central point
    mid_ra = (urra+llra)/2.
    mid_dec = (urdec + lldec)/2.
    phi = mid_ra/180.*np.pi
    th = (90.-mid_dec)/180.*np.pi
    pix = hp.ang2pix(nside,th,phi,nest)  # Pixel at center
    neig = hp.get_all_neighbours(nside,pix,None,nest)  # first 8 neighbors
    allp = set(neig)
    checked_big = set()
    checked_all = set()
    k = 0
    while True:
        if k == 10000:
            raise RuntimeError('Did not converge, increase k')
        temp = allp.copy()
        for i in temp.copy().difference(checked_big):
            ntemp = set(hp.get_all_neighbours(nside,i,None,nest))
            for j in ntemp.difference(checked_all):
                th2,phi2 = hp.pix2ang(nside,j,nest)
                if is_inside_bbox(phi2*180./np.pi,90-th2*180./np.pi,llra,lldec,urra,urdec):
                    temp.add(j)
            checked_all.update(ntemp)
            checked_big.add(i)
        if temp == allp:
            break
        else:
            allp.update(temp)
            k += 1
    all_verts = []
    for i in allp:
        all_verts.append(get_vert(i, nside,nest))
    return all_verts
