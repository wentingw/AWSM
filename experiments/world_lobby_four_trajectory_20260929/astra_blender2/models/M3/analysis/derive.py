exec(open(__file__.replace('derive.py','measure.py')).read().split('for args in')[0])
z=np.array([-.218,.008,.976]);z/=np.linalg.norm(z);y=np.array([.261,.964,.059]);y-=y@z*z;y/=np.linalg.norm(y);x=np.cross(y,z);X=np.eye(4);X[:3,:3]=np.array([x,y,z]);X[2,3]=2.15
print('X',X)
def pix(i,uv):
 f=P['frames'][i];K=np.array(f['intrinsics']);T=np.array(f['camera_to_world']);q=np.linalg.inv(K)@[*uv,1.];q=T[:3,:3]@q;q/=np.linalg.norm(q);return T[:3,3],q
def tri(label,obs):
 A=[];b=[]
 for i,uv in obs:
  o,d=pix(i,uv);a=np.eye(3)-np.outer(d,d);A.append(a);b.append(a@o)
 q=np.linalg.lstsq(np.concatenate(A),np.concatenate(b),rcond=None)[0];res=[];dq=[]
 for i,uv in obs:
  f=P['frames'][i];T=np.array(f['camera_to_world']);c=T[:3,:3].T@(q-T[:3,3]);v=np.array(f['intrinsics'])@c;res.append(float(np.linalg.norm(v[:2]/v[2]-uv)));dq.append((points(i,[uv[0]-4,uv[1]-4,uv[0]+4,uv[1]+4]).mean(0)@X[:3,:3].T+X[:3,3]).tolist())
 qm=q@X[:3,:3].T+X[:3,3];r=dict(label=label,observations=[dict(frame=i,pixel=uv) for i,uv in obs],point_input=q.tolist(),point_model=qm.tolist(),reprojection_errors_px=res,da3_points_model=dq);records.append(r);print(label,'model',qm.round(3),'res',np.round(res,2),'DA3',np.round(dq,2));return qm
tri('crest_top_left',[(33,[606,348]),(129,[962,436]),(155,[640,314])])
tri('crest_bottom',[(33,[622,403]),(129,[985,507]),(155,[656,369])])
tri('desk_left_top',[(33,[543,439]),(129,[842,546]),(155,[573,406])])
tri('desk_right_top',[(33,[688,439]),(129,[1048,560]),(155,[720,406])])
tri('divider_left_front_bottom',[(33,[464,570]),(129,[560,723]),(155,[468,538])])
tri('divider_left_right_bottom',[(33,[599,575]),(129,[730,758]),(155,[603,543])])
tri('divider_right_right_bottom',[(33,[790,579]),(129,[1008,851]),(155,[797,547])])
tri('column_bottom_left',[(33,[252,516]),(129,[355,729]),(155,[253,488])])
tri('mirror_large_left_top',[(61,[742,334]),(74,[870,302])])
for i,box,label in [(33,[20,760,180,940],'floor'),(82,[20,690,350,830],'floor'),(129,[1120,870,1250,940],'floor'),(33,[470,295,550,420],'far_wall'),(91,[390,140,630,225],'near_wall'),(61,[400,150,1100,290],'mirror_wall'),(82,[580,280,770,400],'mirror_wall'),(108,[425,350,610,500],'glazing'),(33,[460,20,680,110],'ceiling'),(82,[850,60,1100,180],'ceiling')]:
 q=points(i,box)@X[:3,:3].T+X[:3,3];print('region',label,i,np.quantile(q,[.05,.5,.95],axis=0).round(3))
(R/'analysis/triangulation.json').write_text(json.dumps(records,indent=2));(R/'analysis/transform.json').write_text(json.dumps(dict(model_from_input=X.tolist(),scale=1),indent=2))
