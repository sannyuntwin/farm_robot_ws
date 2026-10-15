import json
import math
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

_DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Farm Robot Dashboard</title>
<style>
  :root { --bg: #1a1a2e; --card: #16213e; --accent: #00d4ff; --danger: #e94560; --muted: #888; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: #eee; font-family: monospace; padding: 24px; }
  h1 { color: var(--accent); margin-bottom: 20px; font-size: 1.4em; letter-spacing: 1px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; max-width: 680px; }
  .card { background: var(--card); border-radius: 10px; padding: 16px; }
  .card-title { font-size: 0.75em; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
  .row { display: flex; justify-content: space-between; align-items: baseline; margin: 4px 0; }
  .lbl { font-size: 0.8em; color: var(--muted); }
  .val { font-size: 1.1em; color: var(--accent); font-weight: bold; }
  .unit { font-size: 0.75em; color: var(--muted); margin-left: 3px; }
  button { width: 100%; padding: 11px; background: var(--danger); border: none; border-radius: 7px;
           color: #fff; font-size: 0.95em; font-family: monospace; cursor: pointer; margin-top: 10px; }
  button:hover { filter: brightness(1.15); }
  #status { font-size: 0.8em; margin-top: 8px; color: var(--muted); min-height: 1.2em; }
  #dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
         background: #555; margin-right: 6px; vertical-align: middle; }
  #dot.live { background: #00ff88; }
</style>
</head>
<body>
<h1><span id="dot"></span>Farm Robot Dashboard</h1>
<div class="grid">
  <div class="card">
    <div class="card-title">Position</div>
    <div class="row"><span class="lbl">X</span><span><span class="val" id="x">--</span><span class="unit">m</span></span></div>
    <div class="row"><span class="lbl">Y</span><span><span class="val" id="y">--</span><span class="unit">m</span></span></div>
    <div class="row"><span class="lbl">Heading</span><span><span class="val" id="yaw">--</span><span class="unit">deg</span></span></div>
  </div>
  <div class="card">
    <div class="card-title">Velocity</div>
    <div class="row"><span class="lbl">Linear</span><span><span class="val" id="linear">--</span><span class="unit">m/s</span></span></div>
    <div class="row"><span class="lbl">Angular</span><span><span class="val" id="angular">--</span><span class="unit">rad/s</span></span></div>
  </div>
  <div class="card">
    <div class="card-title">LiDAR</div>
    <div class="row"><span class="lbl">Front</span><span><span class="val" id="front">--</span><span class="unit">m</span></span></div>
    <div class="row"><span class="lbl">Left</span><span><span class="val" id="left">--</span><span class="unit">m</span></span></div>
    <div class="row"><span class="lbl">Right</span><span><span class="val" id="right">--</span><span class="unit">m</span></span></div>
  </div>
  <div class="card">
    <div class="card-title">Control</div>
    <button onclick="returnHome()">Return to Home</button>
    <div id="status"></div>
  </div>
</div>
<script>
  const f = v => (v !== null && v !== undefined) ? v : '--';
  const dot = document.getElementById('dot');

  async function update() {
    try {
      const d = await (await fetch('/api/state')).json();
      document.getElementById('x').textContent       = f(d.x);
      document.getElementById('y').textContent       = f(d.y);
      document.getElementById('yaw').textContent     = f(d.yaw);
      document.getElementById('linear').textContent  = f(d.linear);
      document.getElementById('angular').textContent = f(d.angular);
      document.getElementById('front').textContent   = f(d.front);
      document.getElementById('left').textContent    = f(d.left);
      document.getElementById('right').textContent   = f(d.right);
      dot.className = 'live';
    } catch(e) { dot.className = ''; }
  }

  async function returnHome() {
    const st = document.getElementById('status');
    try {
      await fetch('/api/return_home', { method: 'POST' });
      st.textContent = 'Return to home triggered.';
      st.style.color = '#00d4ff';
    } catch(e) {
      st.textContent = 'Request failed.';
      st.style.color = '#e94560';
    }
  }

  setInterval(update, 500);
  update();
</script>
</body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    node = None   # set to the WebDashboard instance after init

    def log_message(self, *_):
        pass   # suppress per-request console output

    def do_GET(self):
        if self.path == '/':
            body = _DASHBOARD_HTML.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/api/state':
            if _Handler.node:
                data = _Handler.node.get_state()
            else:
                data = {}
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/return_home':
            if _Handler.node:
                _Handler.node.trigger_return_home()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()


class WebDashboard(Node):
    def __init__(self):
        super().__init__('web_dashboard')

        self._lock    = threading.Lock()
        self._x       = 0.0
        self._y       = 0.0
        self._yaw     = 0.0
        self._linear  = 0.0
        self._angular = 0.0
        self._front   = None
        self._left    = None
        self._right   = None

        self._home_pub = self.create_publisher(Bool, '/return_home', 10)

        self.create_subscription(Odometry,  '/odom',       self._odom_cb,  10)
        self.create_subscription(Twist,     '/cmd_vel',    self._vel_cb,   10)
        self.create_subscription(LaserScan, '/scan_fixed', self._scan_cb,  10)

        _Handler.node = self
        port   = 8080
        server = HTTPServer(('0.0.0.0', port), _Handler)
        t      = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        self.get_logger().info(f'Dashboard running at http://localhost:{port}')

    def get_state(self):
        with self._lock:
            return {
                'x': self._x, 'y': self._y, 'yaw': self._yaw,
                'linear': self._linear, 'angular': self._angular,
                'front': self._front, 'left': self._left, 'right': self._right,
            }

    def trigger_return_home(self):
        msg = Bool()
        msg.data = True
        self._home_pub.publish(msg)
        self.get_logger().info('Return to home triggered via dashboard.')

    def _odom_cb(self, msg):
        q = msg.pose.pose.orientation
        with self._lock:
            self._x   = round(msg.pose.pose.position.x, 3)
            self._y   = round(msg.pose.pose.position.y, 3)
            self._yaw = round(math.degrees(2.0 * math.atan2(q.z, q.w)), 1)

    def _vel_cb(self, msg):
        with self._lock:
            self._linear  = round(msg.linear.x,  3)
            self._angular = round(msg.angular.z, 3)

    def _sector_min(self, scan, center_deg, half_width_deg):
        dists = []
        for i, d in enumerate(scan.ranges):
            ang = math.degrees(scan.angle_min + i * scan.angle_increment)
            if abs(((ang - center_deg + 180) % 360) - 180) <= half_width_deg:
                if math.isfinite(d) and scan.range_min <= d <= scan.range_max:
                    dists.append(d)
        return round(min(dists), 2) if dists else None

    def _scan_cb(self, scan):
        front = self._sector_min(scan,   0, 25)
        left  = self._sector_min(scan,  90, 20)
        right = self._sector_min(scan, -90, 20)
        with self._lock:
            self._front = front
            self._left  = left
            self._right = right


def main(args=None):
    rclpy.init(args=args)
    node = WebDashboard()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
