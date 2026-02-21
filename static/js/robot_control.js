document.addEventListener('DOMContentLoaded', function(){
  const robot = window.ROBOT || {};
  const map = L.map('robotControlMap').setView([30,110], 6);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(map);

  const dotIcon = L.divIcon({ className: 'map-dot-icon', html: '<span class="map-dot"></span>', iconSize: [14,14], iconAnchor: [7,7] });
  let robotMarker = null;
  let targetMarker = null;

  const statusBadge = document.getElementById('robotStatusBadge');
  const batteryText = document.getElementById('robotBatteryText');
  const batteryBar = document.getElementById('robotBatteryBar');
  const lastHeartbeatEl = document.getElementById('robotLastHeartbeat');
  const positionEl = document.getElementById('robotPosition');
  const targetEl = document.getElementById('robotTarget');
  const logList = document.getElementById('robotLogList');

  function appendLog(msg){
    if(!logList) return;
    const now = new Date();
    const timeStr = now.toTimeString().slice(0,8);
    const item = document.createElement('div');
    item.className = 'robot-log-item';
    item.innerHTML = `<span class="time">${timeStr}</span><span class="text">${msg}</span>`;
    logList.appendChild(item);
    // keep last 50 entries
    while(logList.children.length > 50){
      logList.removeChild(logList.firstChild);
    }
    logList.scrollTop = logList.scrollHeight;
  }

  function fetchRobot(){
    fetch('/api/robot/list').then(r=>r.json()).then(j=>{
      if(!j.ok) return;
      const list = j.robots || [];
      const me = list.find(x=> x.id === robot.id || x.device_id === robot.device_id);
      if(me){
        if(me.lat != null && me.lng != null){
          if(robotMarker){ robotMarker.setLatLng([me.lat, me.lng]); }
          else { robotMarker = L.marker([me.lat, me.lng], { icon: dotIcon }).addTo(map).bindPopup(`<b>${me.name}</b><br>${me.device_id}`); map.setView([me.lat, me.lng], 16); }
        }
        // update battery/status display in title & status card
        document.title = `机器人控制 - ${me.name} (${me.status})`;
        if(statusBadge){
          statusBadge.textContent = me.status || 'UNKNOWN';
          statusBadge.classList.remove('status-online','status-offline');
          if(me.status === 'ONLINE'){ statusBadge.classList.add('status-online'); }
          else { statusBadge.classList.add('status-offline'); }
        }
        if(typeof me.battery !== 'undefined' && me.battery !== null){
          const val = Math.max(0, Math.min(100, Number(me.battery)));
          if(batteryText) batteryText.textContent = val.toFixed(0) + '%';
          if(batteryBar) batteryBar.style.width = val + '%';
        }
        if(positionEl && me.lat != null && me.lng != null){
          positionEl.textContent = `${me.lat.toFixed(5)}, ${me.lng.toFixed(5)}`;
        }
        if(lastHeartbeatEl && me.last_heartbeat){
          lastHeartbeatEl.textContent = me.last_heartbeat;
        }
        if(me.target && me.target.lat != null && me.target.lng != null){
          if(targetEl) targetEl.textContent = `${me.target.lat.toFixed(5)}, ${me.target.lng.toFixed(5)}`;
          if(targetMarker){
            targetMarker.setLatLng([me.target.lat, me.target.lng]);
          } else {
            targetMarker = L.marker([me.target.lat, me.target.lng], { icon: dotIcon }).addTo(map).bindPopup('目标位置');
          }
          // prefill nav inputs if empty
          const navLat = document.getElementById('navLat');
          const navLng = document.getElementById('navLng');
          if(navLat && !navLat.value){ navLat.value = me.target.lat; }
          if(navLng && !navLng.value){ navLng.value = me.target.lng; }
        }
      }
    }).catch(e=>console.warn('fetch robot failed', e));
  }

  // polling every 2s for more responsive control
  fetchRobot();
  setInterval(fetchRobot, 2000);

  // camera stream set
  document.getElementById('btnSetStream').addEventListener('click', function(){
    const url = document.getElementById('streamUrl').value.trim();
    if(!url) return alert('请输入流地址');
    document.getElementById('robotCamera').src = url;
  });

  // movement buttons
  document.querySelectorAll('.ctl-btn').forEach(b=>{
    b.addEventListener('click', ()=>{
      const cmd = b.dataset.cmd;
      appendLog(`发送运动命令: ${cmd}`);
      fetch('/api/robot/control', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: robot.id, command: cmd }) })
        .then(r=>r.json()).then(j=>{ if(!j.ok){ appendLog('命令发送失败'); alert('命令发送失败'); } })
        .catch(()=>{ appendLog('请求失败'); alert('请求失败'); });
    });
  });

  // set navigation via inputs
  document.getElementById('btnSetNav').addEventListener('click', ()=>{
    const lat = parseFloat(document.getElementById('navLat').value);
    const lng = parseFloat(document.getElementById('navLng').value);
    if(isNaN(lat) || isNaN(lng)) return alert('请输入合法坐标');
    appendLog(`设置导航目标: ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    fetch('/api/robot/navigate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: robot.id, lat: lat, lng: lng }) })
      .then(r=>r.json()).then(j=>{ appendLog(j.msg || (j.ok? '导航命令已发送':'导航失败')); alert(j.msg || (j.ok? '已发送':'失败')); }).catch(()=>{ appendLog('请求失败'); alert('请求失败'); });
  });

  // allow map double-click to set navigation target
  map.on('dblclick', function(ev){
    const lat = ev.latlng.lat; const lng = ev.latlng.lng;
    if(!confirm(`确认让设备 ${robot.device_id} 导航到 (${lat.toFixed(5)}, ${lng.toFixed(5)}) ?`)) return;
    appendLog(`地图双击设置导航: ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    fetch('/api/robot/navigate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: robot.id, lat: lat, lng: lng }) })
      .then(r=>r.json()).then(j=>{ appendLog(j.msg || (j.ok? '命令已发送':'失败')); alert(j.msg || (j.ok? '命令已发送':'失败')); }).catch(()=>{ appendLog('请求失败'); alert('请求失败'); });
  });
});
