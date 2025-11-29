// 使用动态导入来兼容不同Node版本
async function preprocessRadioData() {
    let fetch;
    
    // 动态导入node-fetch
    try {
        const nodeFetch = await import('node-fetch');
        fetch = nodeFetch.default;
    } catch (error) {
        console.error('无法加载node-fetch:', error);
        // 如果node-fetch不可用，尝试使用全局fetch（Node 18+）
        if (globalThis.fetch) {
            fetch = globalThis.fetch;
            console.log('使用全局fetch');
        } else {
            throw new Error('没有可用的fetch实现');
        }
    }

    try {
        console.log('🚀 开始获取全球电台数据...');
        
        // 使用多个Radio Browser API端点
        const endpoints = [
            'https://de1.api.radio-browser.info/json/stations?limit=5000',
            'https://at1.api.radio-browser.info/json/stations?limit=5000',
            'https://nl1.api.radio-browser.info/json/stations?limit=5000'
        ];
        
        let allStations = [];
        
        for (const endpoint of endpoints) {
            try {
                console.log(`📡 正在从 ${endpoint} 获取数据...`);
                const response = await fetch(endpoint);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const stations = await response.json();
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
                geo_long: station.geo_long,
                lastCheckTime: station.lastchecktime,
                clickCount: station.clickcount || 0
            }))
            .sort((a, b) => (b.votes || 0) - (a.votes || 0));
        
        console.log(`🧹 数据清洗后剩余 ${processedStations.length} 个有效电台`);
        
        // 保存精选数据
        const curatedOutput = {
            lastUpdated: new Date().toISOString(),
            totalStations: processedStations.length,
            source: 'Radio Browser API',
            regions: ['asia', 'europe', 'americas', 'africa', 'oceania'],
            stations: processedStations
        };
        
        const fs = await import('fs');
        const { fileURLToPath } = await import('url');
        const { dirname, join } = await import('path');
        
        const __filename = fileURLToPath(import.meta.url);
        const __dirname = dirname(__filename);
        const dataDir = join(__dirname, '..', 'data');
        
        // 确保data目录存在
        if (!fs.existsSync(dataDir)) {
            fs.mkdirSync(dataDir, { recursive: true });
        }
        
        const outputPath = join(dataDir, 'curated-stations.json');
        fs.writeFileSync(outputPath, JSON.stringify(curatedOutput, null, 2));
        
        console.log(`💾 精选数据保存完成！共 ${processedStations.length} 个电台`);
        console.log(`📁 文件保存至: ${outputPath}`);
        
        return processedStations;
        
    } catch (error) {
        console.error('❌ 数据预处理失败:', error);
        throw error;
    }
}

// 如果直接运行此文件
if (import.meta.url === `file://${process.argv[1]}`) {
    preprocessRadioData().then(() => {
        console.log('🎉 数据预处理完成！');
        process.exit(0);
    }).catch(error => {
        console.error('💥 预处理失败:', error);
        process.exit(1);
    });
}

export default preprocessRadioData;
