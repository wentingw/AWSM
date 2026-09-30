import {
  BarChart, Button, Callout, Card, CardBody, CardHeader, Grid, H1, H2,
  Row, Stack, Stat, Table, Text, useCanvasAction
} from "cursor/canvas";

const phases = ["Excitation P95 speed", "Excitation P95 acceleration", "Excitation P95 gyro"];
const oldMotion = [0.1347, 0.0672, 0.0739];
const newMotion = [0.4257, 0.5574, 0.1993];

export default function OrbSlamOldVsNew() {
  const dispatch = useCanvasAction();
  return <Stack gap={22} style={{maxWidth: 1120, margin: "0 auto", padding: 24}}>
    <Stack gap={6}>
      <H1>Why the new World Lobby capture initializes ORB-SLAM3</H1>
      <Text tone="secondary">
        Same scene, calibration, route geometry and sensor rates; deliberately stronger early motion and a faster circuit.
      </Text>
      <Row gap={8} wrap>
        <Button variant="primary" onClick={() => dispatch({
          type: "openFile",
          path: "drone-web/runtime/stable_camera_path.py"
        })}>Open motion generator</Button>
        <Button variant="secondary" onClick={() => dispatch({
          type: "openFile",
          path: "stable_orbit_geometry_rebuild_20260925/pose_orbslam3_20260925/SUMMARY.md"
        })}>Open failure audit</Button>
        <Button variant="ghost" onClick={() => dispatch({
          type: "openFile",
          path: "stable_orbit_orb_success_20260929/frozen/inertial_evidence.json"
        })}>Open success evidence</Button>
      </Row>
    </Stack>

    <Callout tone="info" title="The opening loop is intentional">
      After 2 seconds stationary, the new rig follows a 20-second local multiaxis excitation path:
      translation, height, yaw and pitch vary, then return to the route start. It looks like circling in
      place, but it is an initialization maneuver for scale, gravity and IMU-bias observability.
    </Callout>

    <Grid columns={4} gap={16}>
      <Stat value="3.1×" label="Excitation P95 speed increase" />
      <Stat value="8.3×" label="Excitation P95 acceleration increase" tone="success" />
      <Stat value="2.7×" label="Excitation P95 gyro increase" />
      <Stat value="94.55%" label="New trajectory coverage" tone="success" />
    </Grid>

    <H2>Capture design comparison</H2>
    <Table
      headers={["Property", "Old stable orbit", "New ORB-oriented capture"]}
      rows={[
        ["Duration / frames", "360 s / 8,999", "180 s / 4,499"],
        ["Stationary start", "8 s", "2 s"],
        ["Initialization motion", "24 s gentle offsets", "20 s repeated multiaxis motion"],
        ["Max local displacement", "0.351 m", "1.079 m"],
        ["Local path length", "2.107 m", "5.722 m"],
        ["Main circuit", "Same 43.171 m geometry over 320 s", "Same 43.171 m geometry over 156 s"],
        ["Calibration / rates", "1280×960, 25 Hz RGB, 250 Hz IMU", "Identical"],
        ["Final ORB result", "0 final keyframes; empty trajectory", "320 keyframes; 4,254 poses"],
      ]}
      columnAlign={["left", "left", "left"]}
      striped
    />

    <Card>
      <CardHeader trailing="Generator-derived">Early excitation strength</CardHeader>
      <CardBody>
        <Stack gap={8}>
          <BarChart
            categories={phases}
            series={[
              {name: "Old stable orbit", data: oldMotion},
              {name: "New ORB-oriented capture", data: newMotion},
            ]}
            showValues
            height={330}
          />
          <Text size="small" tone="tertiary">
            X-axis: motion statistic · Y-axis: native value. Units by category: m/s, m/s², rad/s.
            Source: stable_camera_path.py sampled at 250 Hz over each initialization phase.
          </Text>
        </Stack>
      </CardBody>
    </Card>

    <H2>Observed estimator behavior</H2>
    <Grid columns={2} gap={18}>
      <Card>
        <CardHeader>Old 360-second sequence</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>Repeated “not enough motion”, “scale too small”, and bad-IMU resets.</Text>
            <Text>Official run: IMU initialized for only 186 / 8,999 rows.</Text>
            <Text>Final atlas: one map with zero retained keyframes; trajectory export was empty.</Text>
          </Stack>
        </CardBody>
      </Card>
      <Card>
        <CardHeader>New 180-second sequence</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>Visual tracking first reaches state 2 at 2.68 s.</Text>
            <Text>IMU initialization first succeeds at 6.48 s and is valid for 4,204 / 4,499 rows.</Text>
            <Text>Final atlas: one persistent map, 320 keyframes and 4,254 trajectory poses.</Text>
          </Stack>
        </CardBody>
      </Card>
    </Grid>

    <Callout tone="warning" title="Causal conclusion">
      The evidence supports an observability failure in the old motion profile, not a camera/IMU
      calibration or synchronization mismatch. The initial loop is useful for this ORB-SLAM3 setup,
      although that exact shape is not uniquely required—any feature-rich, moderate, non-degenerate
      6-DoF excitation can serve the same purpose.
    </Callout>
  </Stack>;
}
