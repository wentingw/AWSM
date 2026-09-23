# 工作进展

## 2026-09-22 · 方案评审 v1

- 创建独立工作区，保留旧项目与发布结果。
- 读取指定 session 的用户要求和最新结果；未复制原始 session 或凭据。
- 三个子任务并行：资产审计、评测协议、相关工作/下游设计；主代理整合并复核关键定义和来源。
- 识别 M2 模型来源混用、M3 实际为 SfM+IMU、M4 待跑，以及 M1 独立 COLMAP 后处理不能归为 Astra 位姿的问题。
- 固定六个主系统与补充消融的设计；保留用户指定 5×4 图，另加独立新视角。
- 保存方案、配置草案、旧资产索引和一手来源。
- 新实验、G1 集成、文章成稿与发布均未执行；空结果目录为预留位置。

下一里程碑：P1 数据/代码隔离与输入合同验证，然后 P2 完整 OpenVINS、M4 深度及基线。

## 2026-09-23 · 仅迁移工作区，等待确认

- 按用户要求将独立工作区迁移至 `/home/hchen/Documents/astraBlenderTest/world_model_blog`。
- 更新工作区路径，保留既有方案和资产索引；旧位置不再保留副本。
- 其余工作等待用户确认，不启动实验、建模、下游任务或发布。

## 2026-09-23 · 用户确认继续执行

- 已获准继续方案，先前等待确认状态结束。
- 正在独立工作区冻结8999帧输入与180个关键帧，固定五个主图视角。
- 并行任务：完整OpenVINS31-clone验证、M4/B2 MapAnything深度、独立GT评测工具。
- GPU推理串行调度；保留既有Blender进程和旧结果。

### 第一批实际结果

- 输入清单已冻结：8999 RGB、180采样帧；五视角预选keyframe索引0/36/72/108/144。
- OpenVINS完整360s已完成；175/180采样帧有可用估计。31-clone改善前60s，但中段仍漂移；首位姿对齐位置RMSE3.196583m，后续主表用统一全程SE3另算。
- ViPE原RGB float32缓存约130GB，本工作区改用原PNG重读+属性缓存，3帧像素逐位一致测试通过。
- M1五视角CPU渲染完成；单次GT辅助Sim3配准仅为形状展示，明确不代表原生米制恢复。
- G1官方资产与预训练步态准备中；独立MuJoCo3.3.7环境已安装。
- M4 8-view联合推理触发显存不足；正在尝试保留联合视图的较小窗口，单图输出不能当作多视图米制主实验。

### 当前实验更新（2026-09-23 下午）

- M4 joint4/overlap2：180帧全部完成，独立Astra v2已有74 named objects，clean verifier已指出缺少脚凳、椅背端面/花盆位置等；正在v3修正。
- M3 joint4/overlap2：175有效帧全部完成（首5帧VIO未初始化，不外推假位姿）。单进程复用模型后87窗口约101秒。独立Astra v2已完成，258 named elements中195为结构装饰件，不能当258个语义实例；clean review进行中。
- M2：8999帧全视频SLAM与180个建模深度已完成，独立Astra v3进行中。剩余逐帧depth从checkpoint续跑，GPU串行调度；已经完成的180帧未重做。
- B2：无外部位姿的calibrated RGB MapAnything 89窗口完成；用重叠预测相机的SE3连接窗口，不做GT或逐窗scale fitting。
- B1/B2/B2p直接TSDF已完成（voxel=5cm, truncation=15cm），各自原生坐标。
- 统一pose评测已排除旧OpenVINS结果，修正Sim3旋转与RPE，并处理纳秒文本舍入丢端点；当前固定样本ATE：M2/B1 0.1175969m；M3/B2p 2.5945236m；B2 0.7909437m。M1原生轨迹NA，M4为GT输入。
- 原生depth共同175帧AbsRel：M2 0.0736088、M3 0.2611966、M4 0.1046583、B2 0.1835702；这些不是最终模型rendered-depth。
- 精确三角面表面距离已修复GT误混预测mesh问题；当前model→GT平均距离B1 .453m、B2 .470m、B2p 1.032m；GT观测射线表面→model分别.211/.395/.676m。M1 Sim3诊断为.306/.337m，须披露GT辅助尺度配准。
- G1官方CPU动力学站立/走路/转向smoke通过；语言检索→路线→真实动态行走在明确标记的合成小场景通过，7.562s、零障碍接触。尚未计为M3任务结果。
- 四旋翼MuJoCo四推力6DOF控制验证通过，三航点末端误差约7mm，未计为M3任务结果。
- OSMesa以用户态解包方式实现CPU机器人录像，无系统安装改动。
- 官方DINOv2 ViT-S/14权重已用校验HTTP ranges下载、CPU加载通过。5张任务reference RGB与5条G1英语约束语言指令已在episodes前冻结，目标GT仅在评测目录。
- 20个新视角是隐藏于前端的GT轨迹扰动视角，可评估新视角渲染；不支持独立场景/新轨迹泛化结论。
- 新结果仍全部在本工作区；旧项目只读。站点与中英稿还在成稿，未外部发布。


## 2026-09-23 · 本地发布包与完整任务结果

- ViPE 全8999帧相机/深度完成；M2/M3/M4模型均冻结并完成统一渲染、180视角model depth、100k几何评价。
- 主六系统指标、B2p配对消融、5×4视角、像素深度误差、轨迹及RGB PSNR/SSIM均生成。RGB统一640×480，不拟合颜色。
- 无人机20实跑：15无碰撞候选到达、5collision；严格/宽松复拍0/20，GT终点均值3.38386m/22.2089deg。DINO仅看参考RGB，目标GT位姿由事后独立评价器读取。
- G1共30受限语言指令（5类目标×6改写）：18模型世界接近成功、12规划失败。两类失败目标保留；没有独立视觉身份确认。
- GT静态几何审计覆盖全部实际轨迹，暴露模型与原场景错位；未宣称GT物理迁移。G1脚底为固定base offset proxy。
- 新视角depth曾发现两个问题：旧compositor Z定义错误，以及代理汇总遗漏有效误差的missing penalty。Root重写evaluate_novel_depth_blender.py实际重跑GT-only BVH，assert9984967triangles，保存100k真实射线，正确GT域、prediction域和penalized MAE。旧数据隔离。
- 中英文章、交互视图选择、3D剖视副本、H264任务演示、源码ZIP和复现说明已集成。桌面/390px手机双语页面及模型加载通过Chromium首轮检查，最终dist再次验收。
- 发布建议为GitHub Pages主站 + Hugging Face完整模型资产。仅准备新仓库部署材料，未创建或覆盖任何远端仓库。

最终dist验收通过：中文/英文 × 桌面/390px移动端，0 JavaScript异常、无页面横向溢出、所有HTML本地链接有效，M3/M4 WebGL模型加载与切换成功，两个H264视频均实际播放并解码。发布内容约46 MiB，复现源码与任务记录ZIP约3.4 MiB。冻结模型SHA核验通过，旧M1哈希保持原值。

## 2026-09-23 · 用户授权公开发布

用户选择GitHub Pages主站与HF大资产分工。HF新仓库Ooliva/astra-world-model-blog上传680文件约759MB完成，冻结revision241d313a264a3353bcb87f9fde30f7ef8a6f5bce。GitHub最初登录wtishere后，按用户要求取消该会话且未创建仓库；改由wentingw官方设备授权，仅public_repo权限，采用main分支Pages部署。

GitHub发布纠正：初次设备客户端仅获得integration身份令牌，创建仓库被GitHub拒绝（403），未产生远端仓库。改用官方GitHub CLI源码核实的OAuth客户端，用户再次授权，实际scope=public_repo。成功创建wentingw/astra-world-model-blog并推送commit9df608e603b0bd1720669890fc5e27ff3799a403，Pages正在从main根目录构建。HF匿名核验681个远端文件（包括.gitattributes），678项manifest及8个原模型SHA匹配。

最终公网验收通过：Pages构建built，11个HTTP资源成功，中文/英文HTML SHA256与部署包相同；两语言桌面+手机浏览器无JS异常、无横向溢出，M3/M4模型加载切换正常，两个视频均实际播放解码。首轮模型等待阈值沿用本地过短，按真实公网加载完成重新验收通过，没有修改模型或伪造通过结果。网站与HF公开地址、提交号见publish/DELIVERY.json。
