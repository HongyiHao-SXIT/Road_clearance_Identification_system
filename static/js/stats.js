document.addEventListener('DOMContentLoaded', function(){
  const pie = echarts.init(document.getElementById('pieChart'));
  const line = echarts.init(document.getElementById('lineChart'));

  // 初始化地图（确保容器存在）
  const map = L.map('statsMap').setView([30, 110], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '&copy; OpenStreetMap contributors'}).addTo(map);

  fetch('/api/stats/summary').then(r=>r.json()).then(data=>{
    if(!data.ok) return;

    // 饼图
    const pieData = (data.pie_data && data.pie_data.length) ? data.pie_data : [{name:'暂无数据', value:1, itemStyle:{color:'#22303a'}}];
    pie.setOption({tooltip:{}, series:[{type:'pie', radius:['40%','70%'], data:pieData, label:{color:'#82b2c6'}}]});

    // 折线
    const labels = (data.line_data && data.line_data.labels) ? data.line_data.labels : [];
    const values = (data.line_data && data.line_data.values) ? data.line_data.values : [];
    if (!labels.length) {
      line.clear();
      line.setOption({graphic: [{ type: 'text', left: 'center', top: '45%', style: {text: '暂无趋势数据', fill: '#6b7280', font: '14px Microsoft YaHei'} }]});
    } else {
      line.setOption({xAxis:{type:'category', data:labels}, yAxis:{type:'value'}, series:[{type:'line', data:values, smooth:true}]});
    }

    // 地图点位（小点样式）
    const dotIcon = L.divIcon({ className: 'map-dot-icon', html: '<span class="map-dot"></span>', iconSize: [10,10], iconAnchor: [5,5] });
    (data.locations||[]).forEach(l=>{
      if (l.lat && l.lng) {
        const m = L.marker([l.lat, l.lng], { icon: dotIcon }).addTo(map);
        m.bindPopup(`<b>任务 ${l.id}</b><br>${l.trash_types}`);
      }
    });

    // 让地图正确渲染
    setTimeout(()=>{ try{ map.invalidateSize(); }catch(e){} }, 300);
  }).catch(e=>console.error(e));
});