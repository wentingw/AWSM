exec(open(__file__.replace('anchors.py','measure.py')).read().split('for args in')[0])
X=np.array(json.loads((R/'analysis/transform.json').read_text())['model_from_input'])
def pix(i,uv):
 f=P['frames'][i];K=np.array(f['intrinsics']);T=np.array(f['camera_to_world']);q=T[:3,:3]@np.linalg.inv(K)@[*uv,1.];return T[:3,3],q
def ray(label,i,uv,axis,value):
 o,d=pix(i,uv);o=X[:3,:3]@o+X[:3,3];d=X[:3,:3]@d;q=o+(value-o[axis])/d[axis]*d
 records.append(dict(label=label,frame=i,pixel=uv,plane_axis=axis,plane_value=value,point_model=q.tolist(),provenance='RGB ray intersect assumed common semantic plane; not independent depth measurement'));print(label,q.round(3));return q
for label,uv,z in [('chair_left',(448,671),.05),('chair_left_back',(480,602),.05),('chair_mid',(533,612),.05),('chair_right',(692,620),.05),('ottoman_rear',(587,564),.48),('table',(577,617),.53),('divider_left',(533,573),.05),('divider_right',(724,574),.05),('grass_window',(263,635),.05),('grass_mirror',(1076,681),.05)]:ray(label,33,uv,2,z)
for label,uv,z in [('chair2_a',(756,763),.05),('chair2_b',(884,804),.05),('chair2_c',(1028,869),.05),('table2',(827,871),.52),('plant_tall',(1242,783),.05)]:ray(label,61,uv,2,z)
for label,uv in [('mirror0',(742,421)),('mirror1',(901,481)),('mirror2',(620,361)),('mirror3',(593,434)),('mirror4',(627,498)),('mirror5',(807,527)),('mirror6',(1040,492)),('mirror7',(1043,394)),('mirror8',(951,318)),('mirror9',(870,373))]:ray(label,61,uv,1,-4.2)
for j,uv in enumerate([(350,31),(461,131),(463,203),(525,215),(562,202),(620,223),(701,221),(786,148),(708,172),(1170,114),(784,230),(591,253),(528,276),(614,287),(657,260),(734,277)]):ray('pendant'+str(j),33,uv,2,4.75)
for i,uv,label in [(108,(716,440),'door_right_centre'),(100,(305,393),'door_left_centre')]:ray(label,i,uv,1,3.85)
(R/'analysis/anchors.json').write_text(json.dumps(records,indent=2))
