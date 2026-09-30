exec(open(__file__.replace('fit_repairs.py','measure_repairs.py')).read().split('obs=')[0])
from scipy.optimize import minimize
# Pixels are from source RGB resized by exactly 0.5; cylinder tangencies are not point correspondences.
col=[(33,150,119,155),(100,150,238,258),(108,150,140,174),(118,150,22,91),(129,150,176,212)]
def cd(q):
 cx,cy,r=q;res=[]
 for i,v,ul,ur in col:
  for u in [ul,ur]:
   o,d=ray(i,u,v);h=np.array([-d[1],d[0]]);h/=np.linalg.norm(h);res.append(abs(np.dot(np.array([cx,cy])-o[:2],h))-r)
 return res
fit=least_squares(cd,[6.75,3.1,.36],bounds=([4,1,.15],[9,4,.8]))
result={'column':{'observations':col,'observation_convention':'frame, row, left_u, right_u at 640x480; tangent planes','before':[6.75,3.1,.36],'after':fit.x.tolist(),'tangent_distance_residuals_m':cd(fit.x),'rms_m':float(np.sqrt(np.mean(np.square(cd(fit.x))))),'uncertainty':'manual silhouette pixels ±3 px; fixed upright circular section inferred'}}
# Named bottom diffuser correspondences; identity hypotheses tested by reprojection.
def project(i,p):
 pc=(np.linalg.inv(T[i])@np.r_[p,1])[:3];uv=K@pc;return uv[:2]/uv[2]
def tri(obs):
 def err(p):return np.concatenate([project(i,p)-[u,v] for i,u,v in obs])
 f=least_squares(err,[6,-2,4]);return {'observations':obs,'point':f.x.tolist(),'reprojection_errors_px':np.linalg.norm(err(f.x).reshape(-1,2),axis=1).tolist()}
result['pendant_wall']=tri([(61,292,64),(74,447,37)])
result['pendant_centre']=tri([(33,392,89),(129,335,67),(155,381,66)])
# Back clearance solve: minimise displacement from input ray-plane anchors, maintain closed upholstery clearance.
A=np.array([[6.49,1.21],[7.17,.99],[6.83,-1.12],[5.60,.86],[6.82,-.39]])
B=np.array([[2.59,-1.39],[2.12,-1.26],[3.24,-1.53],[1.76,-.47]])
C=np.array([[-.9,-.6],[-.85,-1.5],[-.1,-1.75]])
result['seats']={}
for name,pts in [('lounge_a',A),('lounge_b',B),('lounge_c',C)]:
 n=len(pts);d=.95
 constraints=[{'type':'ineq','fun':lambda q,i=i,j=j:np.sum((q.reshape(-1,2)[i]-q.reshape(-1,2)[j])**2)-d*d} for i in range(n) for j in range(i)]
 table={'lounge_a':[5.95,.08],'lounge_b':[2.85,-.4],'lounge_c':[-.05,-.55]}[name]
 constraints += [{'type':'ineq','fun':lambda q,i=i:np.sum((q.reshape(-1,2)[i]-table)**2)-1.07**2} for i in range(n)]
 f=minimize(lambda q:np.sum((q.reshape(-1,2)-pts)**2),pts.ravel(),constraints=constraints,method='SLSQP',options={'ftol':1e-12,'maxiter':500})
 result['seats'][name]={'anchors':pts.tolist(),'centres':f.x.reshape(-1,2).tolist(),'clearance_solve_success':bool(f.success),'provenance':'Ray-plane RGB anchors for A129/B61; previous C anchors; subsequent minimal displacement for .95m centre separation is inferred, NOT DA3 fit.'}
(R/'analysis/repair/fits.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
