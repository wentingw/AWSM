"""CPU navigation in a frozen scene; no GT or target-pose access.

Conservative AABB occupancy, A* and a transparent constrained-language scene
query baseline. The caller must provide only the reconstructed object table.
"""
import heapq, itertools, re
import numpy as np

def inflate_boxes(boxes, radius):
    boxes=np.asarray(boxes,dtype=float).reshape(-1,2,3).copy()
    boxes[:,0]-=radius;boxes[:,1]+=radius
    return boxes

def inside(point, boxes):
    return bool(np.any(np.all(point>=boxes[:,0],axis=1)&np.all(point<=boxes[:,1],axis=1)))

def segment_free(a,b,boxes,step=.05):
    a,b=np.asarray(a),np.asarray(b)
    n=max(2,int(np.ceil(np.linalg.norm(b-a)/step))+1)
    return all(not inside(a+(b-a)*u,boxes) for u in np.linspace(0,1,n))

def astar(start,goal,boxes,bounds,resolution=.2,planar=False,max_expansions=300000):
    start,goal=np.asarray(start,float),np.asarray(goal,float);bounds=np.asarray(bounds,float);boxes=np.asarray(boxes,float).reshape(-1,2,3)
    if np.any(start<bounds[0]) or np.any(start>bounds[1]) or np.any(goal<bounds[0]) or np.any(goal>bounds[1]):return {'status':'outside_bounds','path':[]}
    if inside(start,boxes) or inside(goal,boxes):return {'status':'blocked_endpoint','path':[]}
    if segment_free(start,goal,boxes):return {'status':'success','path':[start.tolist(),goal.tolist()],'expanded':0}
    origin=bounds[0];size=np.ceil((bounds[1]-origin)/resolution).astype(int)
    def cell(p):return tuple(np.rint((p-origin)/resolution).astype(int))
    def world(c):return origin+np.array(c)*resolution
    s,g=cell(start),cell(goal)
    offsets=[d for d in itertools.product((-1,0,1),repeat=3) if d!=(0,0,0) and (not planar or d[2]==0)]
    if planar:g=(g[0],g[1],s[2])
    if not segment_free(start,world(s),boxes) or not segment_free(world(g),goal,boxes):return {'status':'grid_endpoint_blocked','path':[]}
    q=[(0.,s)];cost={s:0.};parent={};visited=set()
    while q and len(visited)<max_expansions:
        _,c=heapq.heappop(q)
        if c in visited:continue
        visited.add(c)
        if c==g:
            cells=[c]
            while c!=s:c=parent[c];cells.append(c)
            path=[start]+[world(c) for c in reversed(cells)]+[goal]
            compact=[path[0]];i=0
            while i<len(path)-1:
                j=len(path)-1
                while j>i+1 and not segment_free(path[i],path[j],boxes):j-=1
                compact.append(path[j]);i=j
            return {'status':'success','path':[p.tolist() for p in compact],'expanded':len(visited)}
        cw=world(c)
        for d in offsets:
            n=tuple(a+b for a,b in zip(c,d));nw=world(n)
            if any(v<0 or v>lim for v,lim in zip(n,size)) or n in visited:continue
            if not segment_free(cw,nw,boxes,step=resolution/4):continue
            new=cost[c]+float(np.linalg.norm(nw-cw))
            if new<cost.get(n,float('inf')):
                cost[n]=new;parent[n]=c;heapq.heappush(q,(new+float(np.linalg.norm(nw-world(g))),n))
    return {'status':'no_path' if not q else 'expansion_limit','path':[],'expanded':len(visited)}

SYNONYMS={'seat':'chair','seats':'chair','chairs':'chair','plants':'plant','tree':'plant','potted':'plant','tables':'table','lights':'lamp','light':'lamp','windows':'window','sofa':'sofa','couch':'sofa','stool':'ottoman','stools':'ottoman','mirrors':'mirror'}
STOP={'find','the','a','an','go','to','and','stop','in','front','of','please','look','for'}
def tokens(s):return [SYNONYMS.get(w,w) for w in re.findall(r'[a-z]+',str(s).lower()) if w not in STOP]
def object_description(o):return ' '.join(str(o.get(k,'')) for k in ['category','label','description','attributes'])
def query_scene(text,objects):
    # IDs are returned only after a language query over reconstructed semantics.
    relation=re.split(r'\b(?:near|nearest to|beside|next to)\b',text.lower(),maxsplit=1)
    wanted=set(tokens(relation[0]));ranked=[]
    for o in objects:
        evidence=set(tokens(object_description(o)));score=len(wanted&evidence)/max(1,len(wanted))
        if score>0:ranked.append([score,o])
    if not ranked:return {'status':'no_semantic_match','candidates':[],'scope':'constrained English category/attribute/near queries'}
    if len(relation)==2:
        lt=set(tokens(relation[1]));landmarks=[o for o in objects if lt&set(tokens(object_description(o))) and 'center' in o]
        if not landmarks:return {'status':'landmark_not_found','candidates':[]}
        for pair in ranked:
            o=pair[1]
            if 'center' in o:
                distances=[np.linalg.norm(np.array(o['center'])-l['center']) for l in landmarks if l['object_id']!=o['object_id']]
                if distances:pair[0]+=0.25/(1+min(distances))
    ranked.sort(key=lambda p:(-p[0],p[1]['object_id']))
    return {'status':'matched','candidates':[{'object_id':o['object_id'],'score':float(s)} for s,o in ranked],'scope':'constrained English category/attribute/near queries'}
