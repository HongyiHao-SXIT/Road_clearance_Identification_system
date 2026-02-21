import requests
import time
import argparse
import cv2


# Simple robot simulator for testing the server's robot endpoints.
# - Auto-registers if device not found
# - Sends heartbeat to /api/robot/heartbeat
# - Simulates navigation when server returns NAVIGATE (moves toward target)
# - Drains battery over time and stops when depleted

def simulate_robot(server='http://127.0.0.1:5000', device_id='SIM_ROBOT_001', name='Simulator',
                   lat=30.50, lng=114.30, battery=90, interval=2.0, use_status=False,
                   auto_register=True, nav_after=None, enable_camera=False):
    """Simulator that can use /heartbeat or /status_update.

    - use_status: when True POSTs to /api/robot/status_update instead of /heartbeat
    - auto_register: try to register automatically if server responds 403
    - nav_after: seconds after start to send a test navigate command (optional)
    """
    heartbeat_url = f"{server}/api/robot/heartbeat"
    status_url = f"{server}/api/robot/status_update"
    register_url = f"{server}/api/robot/register"
    navigate_url = f"{server}/api/robot/navigate"

    print(f"启动机器人模拟: {device_id} -> {'status_update' if use_status else 'heartbeat'}")
    start_time = time.time()

    cap = None
    if enable_camera:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print('无法打开本地摄像头，关闭摄像头模拟')
            cap = None

    try:
        while battery > 0:
            payload = {
                'device_id': device_id,
                'lat': round(lat, 6),
                'lng': round(lng, 6),
                'status': 'ONLINE',
                'battery': round(battery, 1)
            }

            url = status_url if use_status else heartbeat_url

            try:
                r = requests.post(url, json=payload, timeout=5)
                if r.status_code == 403:
                    if auto_register:
                        print('设备未注册，尝试自动注册...')
                        reg = requests.post(register_url, json={'device_id': device_id, 'name': name}, timeout=5)
                        try:
                            jr = reg.json()
                        except Exception:
                            jr = {'ok': False}
                        if jr.get('ok'):
                            print('注册成功，下一次心跳将生效')
                        else:
                            print('注册失败，服务器返回:', jr)
                    else:
                        print('设备未注册，停止发送')
                        break
                else:
                    data = r.json()
                    if data.get('ok'):
                        cmd = data.get('command')
                        target = data.get('target') or {}
                        print(f"[{time.strftime('%H:%M:%S')}] 上报成功 | 电量={battery:.1f}% | 指令={cmd}")
                        if cmd == 'NAVIGATE' and target.get('lat') is not None and target.get('lng') is not None:
                            tlat = float(target['lat']); tlng = float(target['lng'])
                            # move 10% closer each heartbeat
                            lat += (tlat - lat) * 0.1
                            lng += (tlng - lng) * 0.1
                            print(f"    正在前往 ({tlat:.6f}, {tlng:.6f})，当前位置 ({lat:.6f}, {lng:.6f})")
                        elif cmd == 'PICK_TRASH':
                            print('    收到抓取指令（模拟执行）')
                    else:
                        print('服务器响应：', data)

            except requests.exceptions.RequestException as e:
                print('请求失败：', e)

            # OpenCV 摄像头预览（可选）
            if cap is not None:
                ret, frame = cap.read()
                if ret:
                    cv2.imshow(f'Robot Camera - {device_id}', frame)
                    # 按 q 退出模拟
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print('检测到按键 q，停止模拟')
                        break
                else:
                    print('摄像头读取失败，关闭摄像头模拟')
                    cap.release()
                    cv2.destroyAllWindows()
                    cap = None

            # optionally send a test navigate command after nav_after seconds
            if nav_after and (time.time() - start_time) > nav_after:
                try:
                    print('发送测试导航命令到服务器')
                    nav_payload = {'id': None, 'lat': lat + 0.01, 'lng': lng + 0.01}
                    # attempt to resolve robot id via list endpoint
                    try:
                        lid = requests.get(f"{server}/api/robot/list", timeout=3).json()
                        if lid.get('ok') and lid.get('robots'):
                            for rr in lid['robots']:
                                if rr.get('device_id') == device_id:
                                    nav_payload['id'] = rr.get('id')
                                    break
                    except Exception:
                        pass

                    if nav_payload['id']:
                        requests.post(navigate_url, json=nav_payload, timeout=3)
                        print('导航命令发送（通过 list 获取到 id）')
                    else:
                        print('未找到设备 id，无法发送导航命令')
                except Exception as e:
                    print('发送导航命令失败', e)
                nav_after = None

            # battery drain and wait（逐渐下降，直到耗尽）
            battery = max(0.0, battery - 0.1 * (interval / 2.0))
            if battery <= 0:
                print('电量耗尽，模拟结束')
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print('\n模拟终止')
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--server', default='http://127.0.0.1:5000', help='Server base URL')
    p.add_argument('--id', default='SIM_ROBOT_001', help='Device ID')
    p.add_argument('--name', default='Simulator', help='Device name')
    p.add_argument('--lat', type=float, default=30.5)
    p.add_argument('--lng', type=float, default=114.3)
    p.add_argument('--battery', type=float, default=90)
    p.add_argument('--interval', type=float, default=2.0, help='Heartbeat interval seconds')
    p.add_argument('--camera', action='store_true', help='Enable local OpenCV camera preview')
    args = p.parse_args()

    simulate_robot(server=args.server, device_id=args.id, name=args.name,
                   lat=args.lat, lng=args.lng, battery=args.battery,
                   interval=args.interval, enable_camera=args.camera)


if __name__ == '__main__':
    main()