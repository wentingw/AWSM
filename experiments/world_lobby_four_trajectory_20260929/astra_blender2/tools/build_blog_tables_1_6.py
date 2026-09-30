#!/usr/bin/env python3
"""Rebuild the Space report with exactly the reference-blog Tables 1–6."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path("/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929")
WORK = ROOT / "astra_blender2"
SOURCE_HTML = WORK / "provenance/current_live_space/index.html"
SPACE = WORK / "report/space"
OUTPUT_HTML = SPACE / "index.html"
RESULTS = SPACE / "results/blog_tables_1_5"

NATIVE_JSON = ROOT / "evaluation/depth/metrics/modeling_180/metrics.json"
MODEL_JSON = SPACE / "results/model_evaluation.json"
M1_JSON = SPACE / "results/table2_m1/metrics.json"
GEOMETRY_JSON = SPACE / "results/blog_tables_456/tables_4_6.json"
APPEARANCE_JSON = SPACE / "results/blog_tables_456/table5_appearance.json"
CURRENT_M4 = WORK / "evaluation/blog_tables_1_6_current_m4"
CURRENT_M4_MODEL_DEPTH_JSON = CURRENT_M4 / "modeling_180/metrics.json"
CURRENT_M4_GEOMETRY_JSON = CURRENT_M4 / "tables_4_6.json"
CURRENT_M4_APPEARANCE_JSON = CURRENT_M4 / "table5_appearance.json"
REMOTE_VERIFICATION = WORK / "provenance/remote_release/release_verification.json"

METHOD_LABELS = {
    "M1": "M1 · 纯视觉 + Astra",
    "M2": "M2 · ViPE + DA3 + Astra",
    "M3": "M3 · ORB-SLAM3 + DA3 + Astra",
    "M4": "M4 · GT pose + DA3 + Astra",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def table_html(number: int, title: str, headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{cell}</th>" for cell in headers)
    body = "\n".join(
        "<tr>" + "".join(
            f"<th>{cell}</th>" if index == 0 else f"<td>{cell}</td>"
            for index, cell in enumerate(row)
        ) + "</tr>"
        for row in rows
    )
    return (
        f"<h2>Table {number}. {title}</h2>\n"
        f'<div class="scroll"><table id="table{number}">'
        f"<thead><tr>{head}</tr></thead><tbody>\n{body}\n</tbody></table></div>"
    )


def build_data() -> dict:
    native = load(NATIVE_JSON)
    model = load(MODEL_JSON)
    m1 = load(M1_JSON)
    geometry = load(GEOMETRY_JSON)
    appearance = load(APPEARANCE_JSON)
    current_m4_model_depth = load(CURRENT_M4_MODEL_DEPTH_JSON)
    current_m4_geometry = load(CURRENT_M4_GEOMETRY_JSON)
    current_m4_appearance = load(CURRENT_M4_APPEARANCE_JSON)

    table1 = [
        {
            "method": "M1",
            "allowed_inputs": "180 张采样 RGB",
            "geometry_source": "视觉推断，无测量尺度",
            "modeling_role": "推断布局，编写对象与材质",
        },
        {
            "method": "M2",
            "allowed_inputs": "完整 RGB 视频；选取 180 帧建模",
            "geometry_source": "ViPE RGB-only 位姿 → pose-conditioned DA3 深度",
            "modeling_role": "将位姿与深度测量组织为对象化场景",
        },
        {
            "method": "M3",
            "allowed_inputs": "视频、IMU、相机–IMU 标定",
            "geometry_source": "ORB-SLAM3 单目惯性位姿 → pose-conditioned DA3 深度",
            "modeling_role": "结合图像、位姿、深度建模",
        },
        {
            "method": "M4",
            "allowed_inputs": "视频及 GT camera pose",
            "geometry_source": "GT 位姿 → pose-conditioned DA3 深度",
            "modeling_role": "与 M3 相同类型的建模流程",
        },
    ]

    pose = {
        "M1": {"ate_m": None, "rotation_deg": None},
        "M2": {"ate_m": 0.1668, "rotation_deg": 0.3065},
        "M3": {"ate_m": 0.1205, "rotation_deg": 0.1943},
        "M4": {"ate_m": "GT input", "rotation_deg": "GT input"},
    }
    table2 = []
    for method in METHOD_LABELS:
        native_absrel = (
            None if method == "M1"
            else native["methods"][method]["primary_no_scale_fit"]["absrel"]
        )
        if method == "M1":
            model_absrel = m1["aggregate"]["absrel"]
            alignment = "GT-assisted Sim(3), diagnostic only"
        else:
            model_absrel = (
                current_m4_model_depth["aggregate"]["absrel"] if method == "M4"
                else model["splits"]["modeling_180"]["methods"][method]["aggregate"]["absrel"]
            )
            alignment = "GT coordinates" if method == "M4" else "one global SE(3), scale=1"
        table2.append({
            "method": method,
            **pose[method],
            "native_depth_absrel": native_absrel,
            "model_depth_absrel": model_absrel,
            "alignment": alignment,
        })

    table3 = []
    pose_coverage = {"M1": None, "M2": 1.0, "M3": 1.0, "M4": None}
    for method in METHOD_LABELS:
        native_coverage = (
            None if method == "M1"
            else native["methods"][method]["primary_no_scale_fit"]["valid_coverage"]
        )
        model_coverage = (
            m1["aggregate"]["valid_coverage"] if method == "M1"
            else current_m4_model_depth["aggregate"]["valid_coverage"] if method == "M4"
            else model["splits"]["modeling_180"]["methods"][method]["aggregate"]["valid_coverage"]
        )
        table3.append({
            "method": method,
            "sampled_pose_coverage": pose_coverage[method],
            "native_depth_coverage": native_coverage,
            "model_depth_coverage": model_coverage,
        })

    table4 = [
        {
            "method": row["method"],
            "model_to_gt_mean_m": row["model_to_gt"]["mean_m"],
            "observed_gt_to_model_mean_m": row["observed_gt_to_model"]["mean_m"],
            "model_sha256": row["model_sha256"],
            "alignment": row["alignment"],
        }
        for row in geometry["table4"]["rows"]
        if row["method"] in METHOD_LABELS
    ]
    table4 = [row for row in table4 if row["method"] != "M4"]
    current_table4 = current_m4_geometry["table4"]["rows"][0]
    table4.append({
        "method": "M4",
        "model_to_gt_mean_m": current_table4["model_to_gt"]["mean_m"],
        "observed_gt_to_model_mean_m": current_table4["observed_gt_to_model"]["mean_m"],
        "model_sha256": current_table4["model_sha256"],
        "alignment": current_table4["alignment"],
    })
    table5 = [
        {
            "method": row["system"],
            "psnr_db": row["psnr_db_mean"],
            "ssim": row["ssim_mean"],
            "lpips_alex_v01": row["lpips_alex_v01_mean"],
        }
        for row in appearance["rows"]
        if row["system"] in METHOD_LABELS
    ]
    table5 = [row for row in table5 if row["method"] != "M4"]
    current_table5 = current_m4_appearance["rows"][0]
    table5.append({
        "method": "M4",
        "psnr_db": current_table5["psnr_db_mean"],
        "ssim": current_table5["ssim_mean"],
        "lpips_alex_v01": current_table5["lpips_alex_v01_mean"],
    })
    table6 = [
        {
            "method": row["method"],
            "absrel": row["absrel"],
            "rmse_m": row["rmse_m"],
            "coverage": row["valid_coverage"],
            "penalized_mae_m": row["missing_penalty_mae_m"],
        }
        for row in geometry["table6"]["rows"]
        if row["method"] in METHOD_LABELS
    ]
    table6 = [row for row in table6 if row["method"] != "M4"]
    current_table6 = current_m4_geometry["table6"]["rows"][0]
    table6.append({
        "method": "M4",
        "absrel": current_table6["absrel"],
        "rmse_m": current_table6["rmse_m"],
        "coverage": current_table6["valid_coverage"],
        "penalized_mae_m": current_table6["missing_penalty_mae_m"],
    })

    return {
        "schema_version": 1,
        "status": "COMPLETE",
        "scope": "Only frozen models under astra_blender/models/M1..M4",
        "reference": "https://wentingw.github.io/astra-world-model-blog/#_5",
        "m1_notice": (
            "M1 model-space metrics use one frozen GT-assisted Sim(3) from five manual "
            "camera associations. They are diagnostic and do not represent native metric recovery."
        ),
        "protocols": {
            "table2": "180 fixed views × 19,200 pixels; optical-Z; GT-valid domain; no per-view fitting",
            "table3": {
                "model_surface_samples": 100000,
                "model_surface_seed": 20260923,
                "observed_gt_samples": 100000,
                "observed_gt_seed": 20260925,
                "distance": "exact nearest triangle",
            },
            "table4": {
                "views": [0, 36, 72, 108, 144],
                "resolution": [640, 480],
                "gt_resize": "Lanczos 1280x960 to 640x480",
                "metrics": "full-image PSNR, SSIM, LPIPS AlexNet v0.1; no crop/mask/fitting",
            },
            "table5": {
                "views": 20,
                "rays_per_view": 5000,
                "seed": 23,
                "resolution": [640, 480],
                "intrinsics": [381.4, 381.4, 320, 240],
                "depth": "exact BVH optical-Z; GT-valid 0.1–30 m",
            },
        },
        "tables": {
            "table1": table1,
            "table2": table2,
            "table3": table4,
            "table4": table5,
            "table5": table6,
        },
        "source_files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (
                NATIVE_JSON, MODEL_JSON, M1_JSON, GEOMETRY_JSON, APPEARANCE_JSON,
                CURRENT_M4_MODEL_DEPTH_JSON, CURRENT_M4_GEOMETRY_JSON,
                CURRENT_M4_APPEARANCE_JSON,
            )
        },
    }


def build_sections(data: dict) -> tuple[str, str]:
    tables = data["tables"]
    t1 = table_html(1, "四种建模路线与输入信息",
        ["方法", "允许输入", "几何来源", "Astra / Blender 的工作"],
        [[METHOD_LABELS[r["method"]], r["allowed_inputs"], r["geometry_source"], r["modeling_role"]]
         for r in tables["table1"]])
    t2_rows = []
    for row in tables["table2"]:
        ate = "—" if row["ate_m"] is None else ("GT 输入" if row["ate_m"] == "GT input" else f'{row["ate_m"]:.4f}')
        rotation = "—" if row["rotation_deg"] is None else ("GT 输入" if row["rotation_deg"] == "GT input" else f'{row["rotation_deg"]:.4f}')
        native = "—" if row["native_depth_absrel"] is None else pct(row["native_depth_absrel"])
        model = pct(row["model_depth_absrel"])
        if row["method"] == "M3":
            ate, rotation = f"<strong>{ate}</strong>", f"<strong>{rotation}</strong>"
        if row["method"] == "M4":
            native, model = f"<strong>{native}</strong>", f"<strong>{model}</strong>"
        label = METHOD_LABELS[row["method"]]
        if row["method"] == "M1":
            label += " / GT 辅助 Sim(3)†"
        t2_rows.append([label, ate, rotation, native, model])
    t2 = table_html(2, "相机位姿和深度误差",
        ["方法", "ATE (m) ↓", "Rotation (°) ↓", "Native depth AbsRel ↓", "Model depth AbsRel ↓"],
        t2_rows)
    early = f"""
  <section class="notice"><strong>发布范围：</strong>本页只比较
  <code>astra_blender/models/M1–M4</code> 的四个冻结模型，并按参考博客定义报告 Table 1–5。
  M1 的模型空间结果使用一次 GT 辅助 Sim(3)，仅作形状诊断。</section>
  <section id="methods"><p class="eyebrow">01 / PIPELINES</p>{t1}</section>
  <section id="metrics"><p class="eyebrow">02 / POSE AND DEPTH</p>{t2}
    <p>位姿对 M2/M3 使用一次全局 SE(3) 对齐且 scale=1；M4 为 GT 输入。两项深度指标均在
    180 个固定视角、每帧 19,200 个采样位置上计算。<strong>Native depth AbsRel</strong>
    比较 DA3 optical-Z 与 GT；<strong>Model depth AbsRel</strong> 比较冻结 Blender 模型射线深度与 GT。
    † M1 无原生米制位姿或深度，其模型深度只作 GT 辅助 Sim(3) 诊断，不参与原生米制恢复排名。</p>
  </section>
"""

    t3_rows = []
    for row in tables["table3"]:
        left, right = f'{row["model_to_gt_mean_m"]:.4f}', f'{row["observed_gt_to_model_mean_m"]:.4f}'
        if row["method"] == "M4":
            left, right = f"<strong>{left}</strong>", f"<strong>{right}</strong>"
        t3_rows.append([METHOD_LABELS[row["method"]], left, right])
    t3 = table_html(3, "四种建模方法的几何误差",
        ["方法", "Model → GT (m) ↓", "Observed GT → model (m) ↓"], t3_rows)

    t4_rows = []
    for row in tables["table4"]:
        values = [f'{row["psnr_db"]:.4f}', f'{row["ssim"]:.4f}', f'{row["lpips_alex_v01"]:.4f}']
        if row["method"] == "M2":
            values[0], values[2] = f"<strong>{values[0]}</strong>", f"<strong>{values[2]}</strong>"
        if row["method"] == "M3":
            values[1] = f"<strong>{values[1]}</strong>"
        t4_rows.append([METHOD_LABELS[row["method"]], *values])
    t4 = table_html(4, "五个输入视角上的外观指标",
        ["方法", "PSNR (dB) ↑", "SSIM ↑", "LPIPS ↓"], t4_rows)

    t5_rows = []
    for row in tables["table5"]:
        values = [pct(row["absrel"]), f'{row["rmse_m"]:.4f}', pct(row["coverage"]), f'{row["penalized_mae_m"]:.4f}']
        if row["method"] == "M3":
            values[1], values[2] = f"<strong>{values[1]}</strong>", f"<strong>{values[2]}</strong>"
        if row["method"] == "M4":
            values[0], values[3] = f"<strong>{values[0]}</strong>", f"<strong>{values[3]}</strong>"
        t5_rows.append([METHOD_LABELS[row["method"]], *values])
    t5 = table_html(5, "同一场景新视角的深度误差",
        ["方法", "Novel depth AbsRel ↓", "RMSE (m) ↓", "Coverage ↑", "Penalized MAE (m) ↓"], t5_rows)

    late = f"""
    <section id="reference-protocol-evaluation">
      <p class="eyebrow">06 / REFERENCE BLOG PROTOCOLS</p>
      <p class="notice"><strong>M1 配准口径：</strong>使用五个人工相机关联拟合一次 GT 辅助 Sim(3)，
      此后固定用于 Table 2–5；不做网格 ICP 或逐视角调整。该结果仅是形状/展示诊断。</p>
      {t3}
      <p>Model → GT 对模型表面按三角形面积采样 100,000 点（seed=20260923）；
      Observed GT → model 从 180 帧 GT 射线命中中按观测频次采样 100,000 点
      （seed=20260925）。两列均取到另一网格精确最近三角形距离的均值。</p>
      {t4}
      <p>固定输入视角 0/36/72/108/144，统一 GT 相机渲染 640×480；GT RGB 由
      1280×960 Lanczos 缩小。全图计算 PSNR、SSIM 与 LPIPS AlexNet v0.1，
      不裁剪、不遮罩、不拟合颜色或曝光。</p>
      {t5}
      <p>20 个确定性同轨迹扰动相机，每视角固定随机采样 5,000 像素（seed=23）；
      640×480，内参 (381.4, 381.4, 320, 240)。在 GT 网格和冻结模型上做精确 BVH
      optical-Z 射线求交；GT 有效域 0.1–30 m，缺失预测按 30 m 计入惩罚 MAE。</p>
      <p><a href="results/blog_tables_1_5/tables_1_5.json">Table 1–5 完整 JSON</a> ·
      <a href="results/blog_tables_1_5/table1.csv">Table 1 CSV</a> ·
      <a href="results/blog_tables_1_5/table2.csv">Table 2 CSV</a> ·
      <a href="results/blog_tables_1_5/table3.csv">Table 3 CSV</a> ·
      <a href="results/blog_tables_1_5/table4.csv">Table 4 CSV</a> ·
      <a href="results/blog_tables_1_5/table5.csv">Table 5 CSV</a> ·
      <a href="results/blog_tables_456/table5_appearance_per_view.csv">外观 M1–M3 逐视角 CSV</a> ·
      <a href="results/blog_tables_1_6/current_m4/table5_appearance_per_view.csv">外观 M4 逐视角 CSV</a> ·
      <a href="results/blog_tables_1_6/current_m4/tables_4_6.json">当前 M4 几何/新视角完整 JSON</a> ·
      <a href="results/blog_tables_1_6/current_m4/metrics.json">当前 M4 模型深度完整 JSON</a></p>
    </section>
"""
    return early, late


def write_evidence(data: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "tables_1_5.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    for number in range(1, 6):
        rows = data["tables"][f"table{number}"]
        fields = list(rows[0])
        with (RESULTS / f"table{number}.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def build_html(data: dict) -> str:
    source = SOURCE_HTML.read_text()
    early, late = build_sections(data)
    before_main = source.split("<main>", 1)[0]
    figure14 = """
  <section id="figure14">
    <p class="eyebrow">03 / TRAJECTORY DIAGNOSTICS</p>
    <h2>Figure 14. 轨迹、平移误差与旋转误差</h2>
    <figure class="figure-wide">
      <a href="assets/figure14_abc.png"><img src="assets/figure14_abc.png"
        alt="Figure 14 相机轨迹、平移误差与旋转误差组合图"></a>
      <figcaption>Figure 14. (a) GT、ORB-SLAM3、ViPE default 与 OpenVINS 的 XY 轨迹；
      (b) 平移误差；(c) 旋转误差。每个估计器使用一次 SE(3) 对齐，误差曲线为 1 秒移动平均，
      Table 2 的 RMSE 使用全部原始逐帧误差。</figcaption>
    </figure>
    <p class="caption-note">OpenVINS 仅保留为轨迹诊断曲线，不加入仅含 M1–M4 的 Table 2。</p>
  </section>
"""
    reference_figures = """
  <section id="fixed-view-comparisons">
    <p class="eyebrow">04 / FIXED-VIEW COMPARISONS</p>
    <h2>五视角 RGB 对比（参考博客 Figure 5 布局）</h2>
    <figure class="figure-wide">
      <a href="assets/fixed_five_view_comparison_m1_m4.jpg">
        <img loading="lazy" src="assets/fixed_five_view_comparison_m1_m4.jpg"
          alt="M1–M4 与输入 GT 的五视角 RGB 比较"></a>
      <figcaption>行依次为固定建模视角 0、36、72、108、144；列依次为 M1、M2、M3、M4
      和输入 GT。所有预测均使用同一 GT 相机及冻结全局配准，640×480，不做逐视角调整。</figcaption>
    </figure>
    <h2>固定 GT 相机模型深度误差（参考博客 Figure 7 布局）</h2>
    <figure class="figure-wide">
      <a href="assets/model_depth_error_five_views_m1_m4.png">
        <img loading="lazy" src="assets/model_depth_error_five_views_m1_m4.png"
          alt="M1–M4 固定 GT 相机模型深度相对误差热图"></a>
      <figcaption>同一组五个视角与 M1–M4 冻结模型。颜色为
      |预测 optical-Z − GT optical-Z| / GT optical-Z，统一截断到 1.0；
      青色表示缺失或无效预测。</figcaption>
    </figure>
    <p><a href="results/blog_tables_1_5/reference_style_figures.json">图片输入、模型深度来源及哈希</a></p>
  </section>
"""
    blender_start = source.index('<section id="blender-report">')
    old_tables_start = source.index('<h2 id="model-metrics">', blender_start)
    blender_models = source[blender_start:old_tables_start]
    downloads_start = source.index("<h2>逐帧指标与模型深度下载</h2>", old_tables_start)
    evidence_start = source.index('<section id="evidence">', downloads_start)
    downloads = source[downloads_start:evidence_start]
    if downloads.endswith("</section>"):
        downloads = downloads[:-len("</section>")]
    reference_start = source.index('<section id="reference-protocol-evaluation">', evidence_start)
    evidence = source[evidence_start:reference_start]
    if not evidence.rstrip().endswith("</section>"):
        raise RuntimeError("Could not isolate evidence section")
    footer = source[source.index("</main>", reference_start):]

    nav_start = before_main.index("<nav>")
    nav_end = before_main.index("</nav>", nav_start) + len("</nav>")
    new_nav = (
        '<nav><a href="#methods">方法</a><a href="#metrics">位姿与深度</a>\n'
        '  <a href="#figure14">轨迹诊断</a><a href="#fixed-view-comparisons">五视角对比</a>\n'
        '  <a href="#blender-report">模型与渲染</a>\n'
        '  <a href="#reference-protocol-evaluation">几何、外观与新视角</a>\n'
        '  <a href="#evidence">证据</a></nav>'
    )
    header = before_main[:nav_start] + new_nav + before_main[nav_end:]
    blender_models = blender_models.replace(
        'Table 1–11、原报告 Figure 14 与模型 Figure 15–23 现已合并在同一页面；'
        'Table 9–11 复现参考博客 Table 4–6 的计算口径。',
        '页面仅保留连续编号的 Table 1–5；表格、交互模型与统一相机渲染中的 M1–M4 '
        '均严格来自 <code>astra_blender/models/M1–M4</code>。',
    )
    m4_start = blender_models.index(
        '<article class="model-card"><h3>M4 · GT pose + DA3 + Astra</h3>'
    )
    m4_card = """<article class="model-card"><h3>M4 · GT pose + DA3 + Astra</h3>
<figure id="figure22"><model-viewer id="viewer-M4" src="models/M4/preview.glb"
camera-controls touch-action="pan-y" shadow-intensity="0.5" environment-image="neutral"
exposure="1" alt="M4 revision 4 可交互语义模型"></model-viewer>
<figcaption>Figure 22. M4 revision 4 可交互语义模型</figcaption></figure>
<p><button type="button" data-viewer="viewer-M4" data-model="models/M4/preview.glb">交互预览</button>
<button type="button" data-viewer="viewer-M4" data-model="models/M4/scene.glb">完整模型</button></p>
<p>冻结版本：revision 4；状态：<strong>frozen_for_independent_GT_evaluation</strong>。
模型使用米、Z-up、identity input/model transform；包含 74 个语义对象、37 个静态 AABB
碰撞代理和 180 个输入相机。BLEND SHA-256：
<code>cc6cb605246a255d94e36b9dc3f8b91d5a292b047470bc0ff75b8a5c404b0cfe</code>。</p>
<p><a href="models/M4/scene.glb">GLB</a> · <a href="models/M4/scene.blend">Blender</a> ·
<a href="models/M4/source_and_evidence_compact.zip">程序、清单与审查证据</a> ·
<a href="models/M4/modelling_manifest.json">Manifest</a> ·
<a href="models/M4/final_freeze.json">Freeze record</a></p>
<details><summary>审查边界与限制</summary><p>独立审查员检查 revision 2 后要求修改；
建模器在 revision 3/4 回应并冻结。该干净审查未对 revision 4 重新执行完整视觉复审，
因此这里不宣称最终视觉质量通过。材质、隐藏结构、植物细节和物理参数仍包含推断；
碰撞体是静态 AABB 代理。</p></details>
<p><small>冻结后统一 GT 相机渲染</small></p><div class="strip">
<figure id="figure23a"><img loading="lazy" src="views/M4/000.png" alt="M4 revision 4 统一 GT 相机，采样 0"><figcaption>Figure 23(a). M4 统一 GT 相机渲染，采样 0</figcaption></figure>
<figure id="figure23b"><img loading="lazy" src="views/M4/045.png" alt="M4 revision 4 统一 GT 相机，采样 45"><figcaption>Figure 23(b). M4 统一 GT 相机渲染，采样 45</figcaption></figure>
<figure id="figure23c"><img loading="lazy" src="views/M4/090.png" alt="M4 revision 4 统一 GT 相机，采样 90"><figcaption>Figure 23(c). M4 统一 GT 相机渲染，采样 90</figcaption></figure>
<figure id="figure23d"><img loading="lazy" src="views/M4/135.png" alt="M4 revision 4 统一 GT 相机，采样 135"><figcaption>Figure 23(d). M4 统一 GT 相机渲染，采样 135</figcaption></figure>
<figure id="figure23e"><img loading="lazy" src="views/M4/179.png" alt="M4 revision 4 统一 GT 相机，采样 179"><figcaption>Figure 23(e). M4 统一 GT 相机渲染，采样 179</figcaption></figure>
</div></article>"""
    blender_models = blender_models[:m4_start] + m4_card + "</div>"
    result = (
        header + "<main>\n" + early + figure14 + reference_figures + blender_models + late
        + downloads + "</section>" + evidence + footer
    )
    if result.count("<table") != 5:
        raise RuntimeError(f"Expected exactly 5 tables, found {result.count('<table')}")
    for forbidden in ("Table 6", "Table 7", "Table 8", "Table 9", "Table 10", "Table 11", "M4-blog"):
        if forbidden in result:
            raise RuntimeError(f"Old content survived: {forbidden}")
    return result


def main() -> None:
    data = build_data()
    write_evidence(data)
    OUTPUT_HTML.write_text(build_html(data))
    verification_path = SPACE / "release_verification.json"
    verification = load(REMOTE_VERIFICATION if REMOTE_VERIFICATION.exists() else verification_path)
    verification.update({
        "status": "PASS",
        "table_count": 5,
        "table_rows": {"table1": 4, "table2": 4, "table3": 4, "table4": 4, "table5": 4},
        "table_protocol": "wentingw astra-world-model-blog metrics; coverage table removed; remaining tables renumbered 1–5",
        "model_scope": "astra_blender/models/M1..M4",
        "current_m4_sha256": data["tables"]["table3"][-1]["model_sha256"],
        "old_tables_removed": True,
        "m4_blog_extra_row_removed": True,
    })
    published_paths = [
        OUTPUT_HTML,
        SPACE / "assets/fixed_five_view_comparison_m1_m4.jpg",
        SPACE / "assets/model_depth_error_five_views_m1_m4.png",
        SPACE / "models/M4/scene.blend",
        SPACE / "models/M4/scene.glb",
        SPACE / "models/M4/preview.glb",
        SPACE / "models/M4/modelling_manifest.json",
        SPACE / "models/M4/final_freeze.json",
        SPACE / "models/M4/source_and_evidence_compact.zip",
        *[SPACE / f"views/M4/{frame}.png" for frame in ("000", "045", "090", "135", "179")],
    ] + [
        path for path in RESULTS.rglob("*") if path.is_file()
    ]
    verification.setdefault("files", {}).update({
        str(path.relative_to(SPACE)): sha256(path) for path in published_paths
    })
    verification_path.write_text(json.dumps(verification, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUTPUT_HTML}")
    print(f"Wrote {RESULTS}")


if __name__ == "__main__":
    main()
