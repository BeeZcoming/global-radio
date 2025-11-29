const fs = require('fs');

async function preprocessRadioData() {
    try {
        console.log('开始获取电台数据...');
        
        // 使用多个API端点获取数据
        const endpoints = [
            'https://de1.api.radio-browser.info/json/stations?limit=5000',
            'https://at1.api.radio-browser.info/json/stations?limit=5000',
            'https://nl1.api.radio-browser.info/json/stations?limit=5000'
        ];
        
        let allStations = [];
        
        for (const endpoint of endpoints) {
            try {
                console.log(`正在从 ${endpoint} 获取数据...`);
                const response = await fetch(endpoint);
                if (response.ok) {
                    const stations = await response.json();
                    allStations = allStations.concat(stations);
                    console.log(`从 ${endpoint} 获取到 ${stations.length} 个电台`);
                }
            } catch (error) {
                console.warn(`从 ${endpoint} 获取数据失败:`, error.message);
            }
        }
        
        // 去重
        const uniqueStations = [];
        const seenUUIDs = new Set();
        
        allStations.forEach(station => {
            if (!seenUUIDs.has(station.stationuuid)) {
                seenUUIDs.add(station.stationuuid);
                uniqueStations.push(station);
            }
        });
        
        console.log(`去重后共有 ${uniqueStations.length} 个电台`);
        
        // 数据清洗和优化
        const processedStations = uniqueStations
            .filter(station => {
                // 过滤有效电台
                const hasUrl = station.url_resolved || station.url;
                const hasName = station.name && station.name.trim().length > 0;
                return hasUrl && hasName;
            })
            .map(station => ({
                stationuuid: station.stationuuid,
                name: station.name.trim(),
                country: station.country || 'Unknown',
                countrycode: station.countrycode || '',
                url_resolved: station.url_resolved || station.url,
                tags: (station.tags || '').toLowerCase(),
                language: (station.language || '').toLowerCase(),
                votes: station.votes || 0,
                geo_lat: station.geo_lat,
                geo_long: station.geo_long,
                lastCheckTime: station.lastchecktime,
                clickCount: station.clickcount || 0
            }))
            .sort((a, b) => (b.votes || 0) - (a.votes || 0)); // 按投票数排序
        
        // 保存精选数据
        const curatedOutput = {
            lastUpdated: new Date().toISOString(),
            totalStations: processedStations.length,
            stations: processedStations.slice(0, 10000) // 限制数量
        };
        
        fs.writeFileSync('data/curated-stations.json', JSON.stringify(curatedOutput, null, 2));
        console.log(`精选数据保存完成！共 ${curatedOutput.totalStations} 个电台`);
        
        return processedStations;
        
    } catch (error) {
        console.error('预处理失败:', error);
        throw error;
    }
}

// 如果直接运行此文件
if (require.main === module) {
    preprocessRadioData().catch(console.error);
}

module.exports = preprocessRadioData;
