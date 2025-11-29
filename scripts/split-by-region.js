const fs = require('fs');

const regionCountries = {
    asia: ['China', 'Japan', 'South Korea', 'India', 'Indonesia', 'Thailand', 'Vietnam', 'Malaysia', 'Philippines', 'Singapore', 'Taiwan', 'Hong Kong', 'Macao', 'Bangladesh', 'Pakistan', 'Sri Lanka'],
    europe: ['United Kingdom', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands', 'Sweden', 'Norway', 'Finland', 'Denmark', 'Switzerland', 'Austria', 'Belgium', 'Ireland', 'Portugal', 'Poland', 'Russia', 'Ukraine', 'Czech', 'Hungary', 'Romania', 'Greece'],
    americas: ['United States', 'Canada', 'Mexico', 'Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Venezuela', 'Cuba', 'Ecuador', 'Dominican', 'Guatemala'],
    africa: ['South Africa', 'Egypt', 'Nigeria', 'Kenya', 'Morocco', 'Ethiopia', 'Ghana', 'Tanzania', 'Algeria', 'Uganda', 'Sudan'],
    oceania: ['Australia', 'New Zealand', 'Fiji', 'Papua New Guinea', 'New Caledonia']
};

function splitStationsByRegion(stations) {
    console.log('开始按地区分片数据...');
    
    Object.keys(regionCountries).forEach(region => {
        const regionStations = stations.filter(station => {
            if (!station.country) return false;
            
            return regionCountries[region].some(country => 
                station.country.toLowerCase().includes(country.toLowerCase())
            );
        });
        
        const output = {
            lastUpdated: new Date().toISOString(),
            totalStations: regionStations.length,
            stations: regionStations
        };
        
        fs.writeFileSync(`data/${region}-stations.json`, JSON.stringify(output, null, 2));
        console.log(`${region}地区: ${regionStations.length} 个电台`);
    });
}

// 如果直接运行此文件
if (require.main === module) {
    const data = JSON.parse(fs.readFileSync('data/curated-stations.json', 'utf8'));
    splitStationsByRegion(data.stations);
}

module.exports = splitStationsByRegion;
