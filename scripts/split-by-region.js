// 使用 CommonJS 语法
const fs = require('fs');
const path = require('path');

// 地区与国家映射
const regionCountries = {
    asia: [
        'China', 'Japan', 'South Korea', 'India', 'Indonesia', 'Thailand', 'Vietnam', 
        'Malaysia', 'Philippines', 'Singapore', 'Taiwan', 'Hong Kong', 'Macao',
        'Bangladesh', 'Pakistan', 'Sri Lanka'
    ],
    europe: [
        'United Kingdom', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands', 
        'Sweden', 'Norway', 'Finland', 'Denmark', 'Switzerland', 'Austria', 
        'Belgium', 'Ireland', 'Portugal', 'Poland', 'Russia', 'Ukraine'
    ],
    americas: [
        'United States', 'Canada', 'Mexico', 'Brazil', 'Argentina', 'Chile', 
        'Colombia', 'Peru', 'Venezuela', 'Cuba', 'Ecuador', 'Dominican'
    ],
    africa: [
        'South Africa', 'Egypt', 'Nigeria', 'Kenya', 'Morocco', 'Ethiopia', 
        'Ghana', 'Tanzania', 'Algeria', 'Uganda', 'Sudan'
    ],
    oceania: [
        'Australia', 'New Zealand', 'Fiji', 'Papua New Guinea', 'New Caledonia'
    ]
};

function splitStationsByRegion() {
    try {
        console.log('🌍 开始按地区分片数据...');
        
        const dataDir = path.join(__dirname, '..', 'data');
        
        // 读取主数据文件
        const mainDataPath = path.join(dataDir, 'curated-stations.json');
        if (!fs.existsSync(mainDataPath)) {
            throw new Error('主数据文件不存在，请先运行预处理脚本');
        }
        
        const mainData = JSON.parse(fs.readFileSync(mainDataPath, 'utf8'));
        const stations = mainData.stations;
        
        console.log(`📊 从主数据读取到 ${stations.length} 个电台`);
        
        let totalRegionalStations = 0;
        
        // 为每个地区创建数据文件
        Object.keys(regionCountries).forEach(region => {
            const regionStations = stations.filter(station => {
                if (!station.country || station.country === 'Unknown') return false;
                
                const countryLower = station.country.toLowerCase();
                return regionCountries[region].some(country => 
                    countryLower.includes(country.toLowerCase())
                );
            });
            
            const output = {
                lastUpdated: mainData.lastUpdated,
                totalStations: regionStations.length,
                region: region,
                countries: regionCountries[region],
                stations: regionStations
            };
            
            const outputPath = path.join(dataDir, `${region}-stations.json`);
            fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
            
            console.log(`✅ ${region}地区: ${regionStations.length} 个电台`);
            totalRegionalStations += regionStations.length;
        });
        
        console.log(`📈 地区分片完成！总共 ${totalRegionalStations} 个地区电台`);
        
    } catch (error) {
        console.error('❌ 地区分片失败:', error);
        throw error;
    }
}

// 如果直接运行此文件
if (require.main === module) {
    splitStationsByRegion();
    console.log('🎉 地区分片完成！');
}

module.exports = splitStationsByRegion;
