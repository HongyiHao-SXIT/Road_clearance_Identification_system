document.addEventListener('DOMContentLoaded', function(){
  const robot = window.ROBOT || {};
  const map = L.map('robotControlMap').setView([30,110], 6);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(map);

  const dotIcon = L.divIcon({ className: 'map-dot-icon', html: '<span class="map-dot"></span>', iconSize: [14,14], iconAnchor: [7,7] });
  let robotMarker = null;

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
        // update battery/status display in title
        document.title = `机器人控制 - ${me.name} (${me.status})`;
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
      fetch('/api/robot/control', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: robot.id, command: cmd }) })
        .then(r=>r.json()).then(j=>{ if(!j.ok) alert('命令发送失败'); })
        .catch(()=>alert('请求失败'));
    });
  });

  // set navigation via inputs
  document.getElementById('btnSetNav').addEventListener('click', ()=>{
    const lat = parseFloat(document.getElementById('navLat').value);
    const lng = parseFloat(document.getElementById('navLng').value);
    if(isNaN(lat) || isNaN(lng)) return alert('请输入合法坐标');
    fetch('/api/robot/navigate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: robot.id, lat: lat, lng: lng }) })
      .then(r=>r.json()).then(j=>{ alert(j.msg || (j.ok? '已发送':'失败')); }).catch(()=>alert('请求失败'));
  });

  // allow map double-click to set navigation target
  map.on('dblclick', function(ev){
    const lat = ev.latlng.lat; const lng = ev.latlng.lng;
    if(!confirm(`确认让设备 ${robot.device_id} 导航到 (${lat.toFixed(5)}, ${lng.toFixed(5)}) ?`)) return;
    fetch('/api/robot/navigate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: robot.id, lat: lat, lng: lng }) })
      .then(r=>r.json()).then(j=>{ alert(j.msg || (j.ok? '命令已发送':'失败')); }).catch(()=>alert('请求失败'));
  });
});
