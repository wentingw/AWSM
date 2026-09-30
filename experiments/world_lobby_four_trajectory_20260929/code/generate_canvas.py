#!/usr/bin/env python3
"""Generate the durable Cursor Canvas with fully inline trajectory data."""
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "world_lobby_four_trajectory_20260929"
EVAL = BASE / "evaluation"
CANVAS = Path(
    "/home/hchen/.cursor/projects/home-hchen-Documents-astraBlenderTest/"
    "canvases/world-lobby-four-trajectory.canvas.tsx"
)
ARCHIVE_CANVAS = BASE / "world-lobby-four-trajectory.canvas.tsx"


def main():
    metrics = json.loads((EVAL / "metrics.json").read_text())
    data = np.load(EVAL / "aligned_common_trajectories.npz")
    sample = np.unique(np.linspace(0, len(data["timestamps_ns"]) - 1, 180).astype(int))
    trajectories = {
        "GT": data["gt_position"][sample, :2].round(5).tolist(),
        "ORB-SLAM3": data["orb_slam3_position"][sample, :2].round(5).tolist(),
        "ViPE default": data["vipe_default_position"][sample, :2].round(5).tolist(),
        "OpenVINS": data["openvins_position"][sample, :2].round(5).tolist(),
    }
    summary = {}
    for name, method in metrics["methods"].items():
        summary[name] = {
            "coverage": method["coverage"] * 100,
            "ate": method["se3"]["translation_m"]["rmse"],
            "rotation": method["se3"]["rotation_deg"]["rmse"],
            "scale": method["sim3_diagnostic"]["scale"],
            "sim3ate": method["sim3_diagnostic"]["translation_m"]["rmse"],
        }
    template = r'''import {
  BarChart, Button, Callout, Card, CardBody, CardHeader, Grid, H1, H2,
  Row, Stack, Stat, Table, Text, useCanvasAction, useHostTheme
} from "cursor/canvas";

const trajectories: Record<string, number[][]> = __TRAJECTORIES__;
const summary: Record<string, {coverage:number;ate:number;rotation:number;scale:number;sim3ate:number}> = __SUMMARY__;
const methods = ["ORB-SLAM3", "ViPE default", "OpenVINS"];

function TrajectoryPlot() {
  const theme = useHostTheme();
  const width = 780, height = 470, left = 62, right = 22, top = 24, bottom = 52;
  const all = Object.values(trajectories).flat();
  const xs = all.map(p => p[0]), ys = all.map(p => p[1]);
  const xmin = Math.floor(Math.min(...xs)), xmax = Math.ceil(Math.max(...xs));
  const ymin = Math.floor(Math.min(...ys)), ymax = Math.ceil(Math.max(...ys));
  const sx = (x:number) => left + (x-xmin)/(xmax-xmin)*(width-left-right);
  const sy = (y:number) => height-bottom-(y-ymin)/(ymax-ymin)*(height-top-bottom);
  const path = (points:number[][]) => points.map((p,i) => `${i ? "L" : "M"} ${sx(p[0]).toFixed(2)} ${sy(p[1]).toFixed(2)}`).join(" ");
  const colors: Record<string,string> = {
    "GT": theme.text.primary,
    "ORB-SLAM3": theme.category.orange,
    "ViPE default": theme.category.blue,
    "OpenVINS": theme.category.red,
  };
  const dash: Record<string,string|undefined> = {"ViPE default":"9 4 2 4","OpenVINS":"7 5"};
  const xticks = Array.from({length:6},(_,i)=>xmin+(xmax-xmin)*i/5);
  const yticks = Array.from({length:6},(_,i)=>ymin+(ymax-ymin)*i/5);
  return <Stack gap={8}>
    <Text weight="semibold">Camera trajectories after one global SE(3) alignment</Text>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="GT ORB-SLAM3 ViPE default and OpenVINS XY camera trajectories" style={{width:"100%",height:"auto"}}>
      {xticks.map((v,i)=><g key={`x${i}`}>
        <line x1={sx(v)} y1={top} x2={sx(v)} y2={height-bottom} stroke={theme.stroke.tertiary}/>
        <text x={sx(v)} y={height-bottom+20} textAnchor="middle" fill={theme.text.tertiary} fontSize="11">{v.toFixed(1)}</text>
      </g>)}
      {yticks.map((v,i)=><g key={`y${i}`}>
        <line x1={left} y1={sy(v)} x2={width-right} y2={sy(v)} stroke={theme.stroke.tertiary}/>
        <text x={left-10} y={sy(v)+4} textAnchor="end" fill={theme.text.tertiary} fontSize="11">{v.toFixed(1)}</text>
      </g>)}
      <line x1={left} y1={height-bottom} x2={width-right} y2={height-bottom} stroke={theme.stroke.primary}/>
      <line x1={left} y1={top} x2={left} y2={height-bottom} stroke={theme.stroke.primary}/>
      {Object.entries(trajectories).map(([name,points])=>
        <path key={name} d={path(points)} fill="none" stroke={colors[name]} strokeWidth={name==="GT" ? 2.8 : 2} strokeDasharray={dash[name]}/>
      )}
      <text x={(left+width-right)/2} y={height-8} textAnchor="middle" fill={theme.text.secondary} fontSize="12">World x (m)</text>
      <text x="15" y={(top+height-bottom)/2} textAnchor="middle" transform={`rotate(-90 15 ${(top+height-bottom)/2})`} fill={theme.text.secondary} fontSize="12">World y (m)</text>
      {Object.keys(trajectories).map((name,i)=><g key={`l${name}`} transform={`translate(${width-200},${36+i*22})`}>
        <line x1="0" y1="0" x2="28" y2="0" stroke={colors[name]} strokeWidth={name==="GT" ? 2.8 : 2} strokeDasharray={dash[name]}/>
        <text x="36" y="4" fill={theme.text.secondary} fontSize="12">{name}</text>
      </g>)}
    </svg>
    <Text size="small" tone="tertiary">X-axis: world x (m) · Y-axis: world y (m) · 180 uniformly displayed samples. Source: frozen 180 s session; metrics use all 4,254 exact common frames.</Text>
  </Stack>;
}

export default function WorldLobbyComparison() {
  const dispatch = useCanvasAction();
  return <Stack gap={22} style={{maxWidth:1180,margin:"0 auto",padding:24}}>
    <Stack gap={6}>
      <H1>World Lobby four-trajectory comparison</H1>
      <Text tone="secondary">GT, ORB-SLAM3, ViPE default and OpenVINS on one 180 s RGB/IMU capture</Text>
      <Row gap={8} wrap>
        <Button variant="primary" onClick={()=>dispatch({type:"openFile",path:"world_lobby_four_trajectory_20260929/evaluation/trajectory_comparison.png"})}>Open full figure</Button>
        <Button variant="secondary" onClick={()=>dispatch({type:"openFile",path:"world_lobby_four_trajectory_20260929/evaluation/REPORT.md"})}>Open report</Button>
        <Button variant="ghost" onClick={()=>dispatch({type:"openFile",path:"world_lobby_four_trajectory_20260929/evaluation/metrics.json"})}>Open JSON</Button>
      </Row>
    </Stack>
    <Grid columns={4} gap={16}>
      <Stat value="4,254" label="Exact common frames" />
      <Stat value="94.55%" label="ORB-SLAM3 coverage" />
      <Stat value="100.00%" label="ViPE coverage" tone="success" />
      <Stat value="98.73%" label="OpenVINS coverage" />
    </Grid>
    <Callout tone="info" title="Fair comparison contract">Each estimator receives one global rigid SE(3) alignment with scale fixed to 1. Sim(3) is diagnostic only. Missing poses are never interpolated.</Callout>
    <Card>
      <CardHeader trailing="Figure 14(a) style">XY trajectories · common frames</CardHeader>
      <CardBody><TrajectoryPlot /></CardBody>
    </Card>
    <H2>Quantitative metrics</H2>
    <Table
      headers={["Method","Coverage","ATE RMSE (m)","Rotation RMSE (deg)","Sim(3) scale","Sim(3) ATE (m)"]}
      rows={methods.map(name=>[
        name,
        `${summary[name].coverage.toFixed(2)}%`,
        summary[name].ate.toFixed(4),
        summary[name].rotation.toFixed(4),
        summary[name].scale.toFixed(6),
        summary[name].sim3ate.toFixed(4),
      ])}
      columnAlign={["left","right","right","right","right","right"]}
      rowTone={["success","info","warning"]}
      striped
    />
    <Grid columns={2} gap={20}>
      <Stack gap={6}>
        <Text weight="semibold">SE(3) absolute trajectory error by method</Text>
        <BarChart categories={methods} series={[{name:"ATE RMSE",data:methods.map(n=>summary[n].ate)}]} valueSuffix=" m" showValues height={260}/>
        <Text size="small" tone="tertiary">X-axis: estimator · Y-axis: ATE RMSE (m) · 4,254 strict common frames.</Text>
      </Stack>
      <Stack gap={6}>
        <Text weight="semibold">SE(3) absolute rotation error by method</Text>
        <BarChart categories={methods} series={[{name:"Rotation RMSE",data:methods.map(n=>summary[n].rotation)}]} valueSuffix="°" showValues height={260}/>
        <Text size="small" tone="tertiary">X-axis: estimator · Y-axis: rotation RMSE (degrees) · 4,254 strict common frames.</Text>
      </Stack>
    </Grid>
    <Text size="small" tone="tertiary">Source: lobby_orb_success_20260929T123153, 239.28–419.20 s simulation clock. All estimator outputs were frozen and hashed before GT access.</Text>
  </Stack>;
}
'''
    content = template.replace("__TRAJECTORIES__", json.dumps(trajectories, separators=(",", ":")))
    content = content.replace("__SUMMARY__", json.dumps(summary, separators=(",", ":")))
    CANVAS.write_text(content)
    ARCHIVE_CANVAS.write_text(content)
    print(CANVAS)
    print(ARCHIVE_CANVAS)


if __name__ == "__main__":
    main()
