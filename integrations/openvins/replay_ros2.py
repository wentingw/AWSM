#!/usr/bin/env python3
"""Replay EuRoC-like recorded image/IMU data into ROS2 (no truth input)."""
import argparse, csv, time
from pathlib import Path
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Imu, Image
except ImportError as e:
    raise SystemExit("replay_ros2.py requires ROS2 rclpy and sensor_msgs: "+str(e))

class Replay(Node):
    def __init__(self, root, rate):
        super().__init__('fixed_camera_replay'); self.root=Path(root); self.rate=rate
        self.ip=self.create_publisher(Imu,'/imu0',1000); self.cp=self.create_publisher(Image,'/cam0/image_raw',10)
        self.imu=self._rows('imu0/data.csv'); self.cam=self._rows('cam0/data.csv'); self.i=self.c=0
        self.start_sim=None; self.start_wall=None; self.errors=0; self.timer=self.create_timer(0.0005,self.tick)
    def _rows(self,p):
        with (self.root/p).open(newline='') as f: return [r for r in csv.reader(f) if r and not r[0].startswith('#')]
    def _stamp(self,ns):
        from builtin_interfaces.msg import Time
        t=Time(); t.sec=int(ns//1_000_000_000); t.nanosec=int(ns%1_000_000_000); return t
    def tick(self):
        if self.i>=len(self.imu) and self.c>=len(self.cam): self.get_logger().info(f'replay complete; image_errors={self.errors}'); rclpy.shutdown(); return
        nt=[]
        if self.i<len(self.imu): nt.append((int(self.imu[self.i][0]),'i'))
        if self.c<len(self.cam): nt.append((int(self.cam[self.c][0]),'c'))
        ts,kind=min(nt)
        if self.start_sim is None: self.start_sim=ts; self.start_wall=time.monotonic()
        target=(ts-self.start_sim)/1e9/max(self.rate,1e-9)
        if time.monotonic()-self.start_wall<target: return
        if kind=='i':
            r=self.imu[self.i]; m=Imu(); m.header.stamp=self._stamp(ts); m.header.frame_id='imu_link_flu'
            # simulator FRD -> ROS FLU; units remain rad/s and m/s^2.
            m.angular_velocity.x=float(r[1]); m.angular_velocity.y=-float(r[2]); m.angular_velocity.z=-float(r[3])
            m.linear_acceleration.x=float(r[4]); m.linear_acceleration.y=-float(r[5]); m.linear_acceleration.z=-float(r[6]); self.ip.publish(m); self.i+=1
        else:
            r=self.cam[self.c]; p=self.root/'cam0/data'/r[1]
            try:
                from PIL import Image as PILImage
                im=PILImage.open(p).convert('RGB'); raw=im.tobytes(); h,w=im.height,im.width
            except Exception as e: self.errors+=1; self.get_logger().error(f'image {p}: {e}'); self.c+=1; return
            m=Image(); m.header.stamp=self._stamp(ts); m.header.frame_id='camera_optical'; m.height=h; m.width=w; m.encoding='rgb8'; m.is_bigendian=0; m.step=w*3; m.data=raw; self.cp.publish(m); self.c+=1
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('dataset',type=Path); ap.add_argument('--rate',type=float,default=1.0); a=ap.parse_args()
    rclpy.init(); r=Replay(a.dataset,a.rate)
    try: rclpy.spin(r)
    finally:
        if rclpy.ok(): rclpy.shutdown()
    if r.errors: raise SystemExit(f'replay failed: {r.errors} image errors')
if __name__=='__main__': main()
