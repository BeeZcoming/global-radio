// 使用 CommonJS 语法
const fs = require('fs');
const path = require('path');

function verifyData() {
    console.log('🔍 开始验证数据文件...');
    
    const dataDir = path.join(__dirname, '..', 'data');
    
    const files = [
        'curated-stations.json',
        'asia-stations.json',
        'europe-stations.json',
        'americas-stations.json',
        'africa-stations.json',
        'oceania-stations.json'
    ];
    
    let totalStations = 0;
    let allFilesValid = true;
    
    files.forEach(file => {
        const filePath = path.join(dataDir, file);
        
        if (fs.existsSync(filePath)) {
            try {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                const stationCount = data.totalStations || 0;
                totalStations += stationCount;
                
                console.log(`✅ ${file}: ${stationCount} 个电台，更新于 ${new Date(data.lastUpdated).toLocaleString()}`);
                
            } catch (error) {
                console.error(`❌ ${file}: JSON解析失败 - ${error.message}`);
                allFilesValid = false;
            }
        } else {
            console.warn(`⚠️ ${file}: 文件不存在`);
            allFilesValid = false;
        }
    });
    
    console.log(`📊 所有数据文件总计: ${totalStations} 个电台`);
    
    if (allFilesValid) {
        console.log('🎉 所有数据文件验证通过！');
    } else {
        console.log('💥 部分数据文件存在问题，请检查！');
        process.exit(1);
    }
}

// 如果直接运行此文件
if (require.main === module) {
    verifyData();
}

module.exports = verifyData;
