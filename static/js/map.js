$(document).ready(function () {
    const map = L.map('map').setView([30.0, 110.0], 5);
    // expose map globally for index updates
    window._indexMap = map;


    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // small dot icon for compact markers (CSS updated for contrast)
    const dotIcon = L.divIcon({ className: 'map-dot-icon', html: '<span class="map-dot"></span>', iconSize: [14,14], iconAnchor: [7,7] });

    // robot markers store
    window._robotMarkers = window._robotMarkers || {};

    function loadDashboardData() {
        fetch('/api/stats/summary')
            .then(res => res.json())
            .then(data => {
                if (!data.ok) return;

                if (data.locations && data.locations.length > 0) {
                    data.locations.forEach(loc => {
                        const marker = L.marker([loc.lat, loc.lng], { icon: dotIcon }).addTo(map);

                        const cardHtml = `
                            <div class="map-card" style="width: 200px; padding: 5px;">
                                <h4 style="margin: 0 0 8px; color: #2563eb; border-bottom: 1px solid #eee;">任务 #${loc.id}</h4>
                                <p style="font-size: 13px; margin: 4px 0;">
                                    <b>识别结果:</b> <span style="color: #ef4444;">${loc.trash_types || '未检测到'}</span>
                                </p>
                                <hr style="border: 0; border-top: 1px solid #eee; margin: 8px 0;">
                                <p style="font-size: 11px; color: #666;">坐标: ${loc.lat.toFixed(4)}, ${loc.lng.toFixed(4)}</p>
                            </div>
                        `;

                        marker.bindPopup(cardHtml, {
                            closeButton: false,
                            offset: L.point(0, -15)
                        });

                        marker.on('mouseover', function () { this.openPopup(); });
                        marker.on('mouseout', function () { this.closePopup(); });
                    });
                }

                // update robot markers if provided by server
                if (data.robot_list && data.robot_list.length > 0) {
                    updateRobotMarkers(data.robot_list);
                }
            })
            .catch(err => console.error("地图数据加载失败:", err));
    }

    // update robot markers function exposed globally
    function updateRobotMarkers(robots) {
        const existingIds = new Set(Object.keys(window._robotMarkers));
        robots.forEach(r => {
            // ensure r has lat/lng
            if (r.lat == null || r.lng == null) return;
            const id = r.device_id || r.id;
            existingIds.delete(id);
            if (window._robotMarkers[id]) {
                // update location and popup
                window._robotMarkers[id].setLatLng([r.lat, r.lng]);
                window._robotMarkers[id].getPopup() && window._robotMarkers[id].setPopupContent(`<b>${r.name}</b><br>${r.device_id}<br>${r.status} ${r.battery!=null? r.battery+'%':''}`);
            } else {
                const m = L.marker([r.lat, r.lng], { icon: dotIcon }).addTo(map).bindPopup(`<b>${r.name}</b><br>${r.device_id}<br>${r.status} ${r.battery!=null? r.battery+'%':''}`);
                m.on('click', ()=>{});
                window._robotMarkers[id] = m;
            }
        });

        // remove markers for robots not present
        existingIds.forEach(id => {
            try { map.removeLayer(window._robotMarkers[id]); } catch(e){}
            delete window._robotMarkers[id];
        });
    }


    loadDashboardData();
    setTimeout(function () {
        map.invalidateSize(true);
    }, 500);

    $(window).on('resize', function () {
        map.invalidateSize();
    });
});