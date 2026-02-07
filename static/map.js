$(document).ready(function () {
    const map = L.map('map').setView([30.0, 110.0], 5);


    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    function loadDashboardData() {
        fetch('/api/stats/summary')
            .then(res => res.json())
            .then(data => {
                if (!data.ok) return;

                if (data.locations && data.locations.length > 0) {
                    data.locations.forEach(loc => {
                        const marker = L.marker([loc.lat, loc.lng]).addTo(map);

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


                    //map.setView([data.locations[0].lat, data.locations[0].lng], 10);
                }
            })
            .catch(err => console.error("地图数据加载失败:", err));
    }


    loadDashboardData();
    setTimeout(function () {
        map.invalidateSize(true);
        console.log("地图尺寸已重新适配");
    }, 500);

    $(window).on('resize', function () {
        map.invalidateSize();
    });
});