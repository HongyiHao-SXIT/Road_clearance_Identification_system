$(function () {
    // 初始化 ECharts
    const trashTypeChart = echarts.init(document.getElementById('trashTypeChart'));
    const workTrendChart = echarts.init(document.getElementById('workTrendChart'));
    const robotBatteryChart = echarts.init(document.getElementById('robotBatteryChart'));

    function refreshData() {
        $.get('/api/stats/summary', function (res) {
            if (!res.ok) return;

            // 1. 填充垃圾分布饼图
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

            // 2. 填充捡拾趋势折线图
            workTrendChart.setOption({
                tooltip: { trigger: 'axis' },
                xAxis: { type: 'category', data: res.line_data.labels, axisLabel: {color: '#82b2c6'} },
                yAxis: { type: 'value', axisLabel: {color: '#82b2c6'}, splitLine: {lineStyle: {color: '#1f2937'}} },
                series: [{
                    data: res.line_data.values,
                    type: 'line',
                    smooth: true,
                    areaStyle: { color: 'rgba(56, 154, 244, 0.2)' },
                    lineStyle: { color: '#389af4' }
                }]
            });

            // 4. 填充左侧机器人状态列表
            const $list = $('#robotListContainer');
            $list.empty();
            res.robot_list.forEach(r => {
                const color = r.status === 'ONLINE' ? '#3de5cc' : '#ff4d4d';
                $list.append(`
                    <li class="tr_item">
                        <span>${r.device_id}</span>
                        <span>${r.name}</span>
                        <span style="color: ${color}">${r.status === 'ONLINE' ? '● 在线' : '● 离线'}</span>
                    </li>
                `);
            });
        });
    }

    // 自动重绘
    window.onresize = function() {
        trashTypeChart.resize();
        workTrendChart.resize();
        robotBatteryChart.resize();
    };

    refreshData();
    setInterval(refreshData, 10000); // 10秒刷新一次数据
});