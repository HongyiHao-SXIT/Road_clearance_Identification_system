document.addEventListener('DOMContentLoaded', function(){
  const addBtn = document.getElementById('addRobotBtn');
  const deviceInput = document.getElementById('newDeviceId');
  const nameInput = document.getElementById('newName');
  const table = document.getElementById('robotTableBody');
  const mapContainer = document.getElementById('robotMap');

  // markers keyed by robot id
  const markers = {};
  let selectedRobotId = null;

  // init leaflet map
  let map = null;
  try {
    map = L.map('robotMap').setView([30,110],5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(map);

    // small dot icon for compact markers
    window._td_dotIcon = L.divIcon({
      className: 'map-dot-icon',
      html: '<span class="map-dot"></span>',
      iconSize: [10, 10],
      iconAnchor: [5, 5]
    });
  } catch(e) { console.warn('Leaflet init failed', e); }

  function setSelectedRow(id){
    selectedRobotId = id;
    table.querySelectorAll('tr').forEach(r=> r.classList.remove('selected'));
    const row = table.querySelector(`tr[data-id='${id}']`);
    if(row) row.classList.add('selected');
  }

  function loadRobots(){
    fetch('/api/robot/list').then(r=>r.json()).then(j=>{
      if(!j.ok) return;
      // update table rows (update status/battery/ip/last-heartbeat by named cells)
      j.robots.forEach(r=>{
        const row = table.querySelector(`tr[data-id='${r.id}']`);
        if(row){
          const s = row.querySelector('.col-status'); if(s) s.innerText = r.status || '-';
          const b = row.querySelector('.col-battery'); if(b) b.innerText = (r.battery!=null? r.battery : '-');
          const ip = row.querySelector('.col-ip'); if(ip) ip.innerText = r.ip_address || '-';
          const last = row.querySelector('.col-last'); if(last) last.innerText = r.last_heartbeat ? new Date(r.last_heartbeat).toLocaleString() : '-';
        }

        // update marker
        if(map && r.lat != null && r.lng != null){
          if(markers[r.id]){
            markers[r.id].setLatLng([r.lat, r.lng]);
          } else {
            const m = L.marker([r.lat, r.lng], { icon: window._td_dotIcon || undefined }).addTo(map).bindPopup(`<b>${r.name}</b><br>${r.device_id}`);
            m.on('click', ()=> setSelectedRow(r.id));
            markers[r.id] = m;
          }
        }
      });
    }).catch(e=>console.warn('fetch robots failed', e));
  }

  // poll robots every 5s
  setInterval(loadRobots, 5000);
  loadRobots();

  // double-click map to send navigate command to selected robot
  if(map){
    map.on('dblclick', function(ev){
      if(!selectedRobotId){ alert('请先在表格中选择一个机器人（单击行或标记）'); return; }
      const lat = ev.latlng.lat; const lng = ev.latlng.lng;
      if(!confirm(`确认让设备 ${selectedRobotId} 导航到 (${lat.toFixed(5)}, ${lng.toFixed(5)}) ?`)) return;
      fetch('/api/robot/navigate', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({id: parseInt(selectedRobotId), lat: lat, lng: lng})
      }).then(r=>r.json()).then(j=>{
        alert(j.msg || (j.ok? '命令已发送':'失败'));
      }).catch(()=>alert('请求失败'));
    });
  }

  addBtn.addEventListener('click', function(){
    const device_id = deviceInput.value.trim();
    const name = nameInput.value.trim();
    if(!device_id || !name){ alert('请填写设备ID和名称'); return; }
    fetch('/api/robot/register', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({device_id, name})
    }).then(r=>r.json()).then(j=>{
      if(j.ok){ location.reload(); } else { alert(j.msg || '添加失败'); }
    }).catch(e=>alert('请求失败'));
  });

  table.querySelectorAll('.btn-delete').forEach(btn=>{
    btn.addEventListener('click', function(){
      const id = this.closest('tr').dataset.id;
      if(!confirm('确认删除该机器人？')) return;
      fetch('/api/robot/delete/'+id, {method:'POST'}).then(r=>r.json()).then(j=>{
        if(j.ok){ location.reload(); } else { alert(j.msg || '删除失败'); }
      }).catch(()=>alert('请求失败'));
    });
  });

  table.querySelectorAll('.btn-nav').forEach(btn=>{
    btn.addEventListener('click', function(){
      const id = this.closest('tr').dataset.id;
      const lat = prompt('目标纬度');
      const lng = prompt('目标经度');
      if(!lat || !lng) return;
      fetch('/api/robot/navigate', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({id: parseInt(id), lat: parseFloat(lat), lng: parseFloat(lng)})
      }).then(r=>r.json()).then(j=>{
        alert(j.msg || (j.ok? '已发送':'失败'));
      }).catch(()=>alert('请求失败'));
    });
  });

  // allow row click to select robot
  table.querySelectorAll('tr[data-id]').forEach(r=>{
    r.addEventListener('click', ()=> setSelectedRow(r.dataset.id));
  });
});