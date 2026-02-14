$(function () {
    const trashTypeChart = echarts.init(document.getElementById('trashTypeChart'));
    function refreshData() {
        $.get('/api/stats/summary', function (res) {
            if (!res.ok) return;

            trashTypeChart.setOption({
                tooltip: { trigger: 'item' },
                series: [{
                    type: 'pie',
                    radius: ['40%', '70%'],
                    data: res.pie_data,
                    label: { color: '#82b2c6' },
                    itemStyle: { borderRadius: 5 }
                }]
            });

            const $list = $('#robotListContainer');
            $list.empty();
            (res.robot_list || []).forEach(r => {
                const color = r.status === 'ONLINE' ? '#3de5cc' : '#ff4d4d';
                $list.append(`
                    <li class="list-item">
                        <span>${r.device_id}</span>
                        <span>${r.name}</span>
                        <span style="color: ${color}">${r.status === 'ONLINE' ? '● 在线' : '● 离线'}</span>
                    </li>
                `);
            });

            // update robot markers on the map if available
            if (window.updateRobotMarkers && res.robot_list) {
                // ensure lat/lng fields exist (stats_api now includes lat/lng)
                window.updateRobotMarkers(res.robot_list);
            }
        });
    }

    window.onresize = function () {
        try { trashTypeChart.resize(); } catch(e){}
        if (typeof workTrendChart !== 'undefined' && workTrendChart) { try { workTrendChart.resize(); } catch(e){} }
        if (typeof robotBatteryChart !== 'undefined' && robotBatteryChart) { try { robotBatteryChart.resize(); } catch(e){} }
    };

    refreshData();
    // poll every 3 seconds for realtime status (matches server-side 3s timeout)
    setInterval(refreshData, 3000);
});

function updateTime() {
    var now = new Date();
    var timeStr = now.getFullYear() + '-' + (now.getMonth() + 1).toString().padStart(2, '0') + '-' + now.getDate().toString().padStart(2, '0') + ' ' +
        now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0') + ':' + now.getSeconds().toString().padStart(2, '0');
    $('.header-date').text(timeStr);
    var weeks = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
    $('.header-week').text(weeks[now.getDay()]);
}
setInterval(updateTime, 1000);
updateTime();