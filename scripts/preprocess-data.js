// 使用 CommonJS 语法避免 ES 模块问题

const fs = require('fs');
const path = require('path');

async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.warn(`尝试 ${i + 1}/${retries} 失败: ${error.message}`);
            if (i < retries - 1) {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
    }
    throw new Error(`无法从 ${url} 获取数据`);
}

async function preprocessRadioData() {
    const dataDir = path.join(__dirname, '..', 'data');

    // 确保data目录存在
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
        console.log('创建 data 目录');
    }

    try {
        console.log('🚀 开始获取全球电台数据...');
        
        // 使用可靠的API端点
        const endpoints = [
            'https://de1.api.radio-browser.info/json/stations?limit=1000&hidebroken=true',
            'https://at1.api.radio-browser.info/json/stations?limit=1000&hidebroken=true'
        ];
        
        let allStations = [];
        
        for (const endpoint of endpoints) {
            try {
                console.log(`📡 正在从 ${endpoint} 获取数据...`);
                const stations = await fetchWithRetry(endpoint);
                console.log(`✅ 从 ${endpoint} 获取到 ${stations.length} 个电台`);
                allStations = allStations.concat(stations);
                
                // 添加延迟避免请求过快
                await new Promise(resolve => setTimeout(resolve, 1000));
                
            } catch (error) {
                console.warn(`❌ 从 ${endpoint} 获取数据失败:`, error.message);
            }
        }
        
        if (allStations.length === 0) {
            throw new Error('无法从任何端点获取数据');
        }
        
        console.log(`📊 总共获取到 ${allStations.length} 个电台`);
        
        // 数据去重
        const uniqueStations = [];
        const seenUUIDs = new Set();
        
        for (const station of allStations) {
            if (!station.stationuuid) continue;
            
            if (!seenUUIDs.has(station.stationuuid)) {
                seenUUIDs.add(station.stationuuid);
                uniqueStations.push(station);
            }
        }
        
        console.log(`🔄 去重后剩余 ${uniqueStations.length} 个电台`);
        
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
                tags: (station.tags || '').toLowerCase().substring(0, 100),
                language: (station.language || '').toLowerCase(),
                votes: station.votes || 0,
                geo_lat: station.geo_lat,
                geo_long: station.geo_long
            }))
            .sort((a, b) => (b.votes || 0) - (a.votes || 0));
        
        console.log(`🧹 数据清洗后剩余 ${processedStations.length} 个有效电台`);
        
        // 保存精选数据
        const curatedOutput = {
            lastUpdated: new Date().toISOString(),
            totalStations: processedStations.length,
            source: 'Radio Browser API',
            stations: processedStations
        };
        
        const outputPath = path.join(dataDir, 'curated-stations.json');
        fs.writeFileSync(outputPath, JSON.stringify(curatedOutput, null, 2));
        
        console.log(`💾 精选数据保存完成！共 ${processedStations.length} 个电台`);
        
        return processedStations;
        
    } catch (error) {
        console.error('❌ 数据预处理失败:', error);
        throw error;
    }
}

// 如果直接运行此文件
if (require.main === module) {
    preprocessRadioData().then(() => {
        console.log('🎉 数据预处理完成！');
        process.exit(0);
    }).catch(error => {
        console.error('💥 预处理失败:', error);
        process.exit(1);
    });
}

module.exports = preprocessRadioData;
