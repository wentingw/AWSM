import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
v=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],float);t=np.array([[0,1,2]],int);b=BVHTree.FromPolygons(v,t,all_triangles=True);d=b.find_nearest(Vector((.25,.25,1.)))[3];print('d',d);d2=b.find_nearest(Vector((.25,.25,.1)))[3];print('d2',d2);print({'triangle_surface_distance_m':d,'units':'metres','status':'PASS'})
