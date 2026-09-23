"""Schedule independent no-VDA depth frames by true index, keyframes first.

The upstream depth equations and whole-trajectory UV branch are unchanged.
Only enumerate(data_iterator) becomes an explicit original-frame index.
"""
import inspect,textwrap,types,hashlib
import cv2,torch
from vipe.streams.base import VideoFrame
from vipe.utils.cameras import CameraType

def scheduled_depth(processor, files, poses, intrinsics, phase="all", skip=()) :
    assert processor.video_depth_model is None, 'Frame reordering is valid only without video-depth temporal state'
    source=textwrap.dedent(inspect.getsource(type(processor).update_iterator))
    old='for frame_idx, frame in pbar(enumerate(data_iterator), desc="Aligning depth"):'
    assert source.count(old)==1, 'Upstream processor changed; review before adapting'
    source=source.replace(old,'for frame_idx, frame in pbar(data_iterator, desc="Aligning depth"):')
    namespace=dict(type(processor).update_iterator.__globals__)
    exec(compile(source,'<indexed_upstream_depth>','exec'),namespace)
    run=types.MethodType(namespace['update_iterator'],processor)
    selected=list(range(0,len(files),50)); chosen=set(selected)
    order=selected if phase=="keyframes" else [i for i in range(len(files)) if i not in chosen] if phase=="rest" else selected+[i for i in range(len(files)) if i not in chosen]
    order=[i for i in order if i not in set(skip)]
    def inputs():
        for i in order:
            bgr=cv2.imread(str(files[i]))
            if bgr is None: raise OSError(str(files[i]))
            rgb=(torch.as_tensor(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)).float()/255.0).cuda()
            yield i,VideoFrame(raw_frame_idx=i,rgb=rgb,pose=poses[i],intrinsics=intrinsics,camera_type=CameraType.PINHOLE)
    return zip(order,run(inputs(),0)),len(selected),hashlib.sha256(source.encode()).hexdigest()
