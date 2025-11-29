name: Update Radio Data

on:
  schedule:
    - cron: '0 2 * * 1'  # 每周一凌晨2点（UTC）自动更新
  workflow_dispatch:      # 允许手动触发
  push:
    branches: [ main ]
    paths:
      - 'scripts/**'      # 脚本更新时也触发

jobs:
  update-data:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
        fetch-depth: 0
        
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        
    - name: Install dependencies
      run: npm install
      
    - name: Run data preprocessing
      run: npm run preprocess
      env:
        NODE_OPTIONS: '--max_old_space_size=4096'
        
    - name: Split data by region
      run: npm run split
      
    - name: Verify data
      run: npm run verify
      
    - name: Commit and push if changed
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add data/
        git diff --staged --quiet && echo "没有数据变化" || (git commit -m "🤖 Auto-update radio data [skip ci]" && git push)
        
    - name: Create summary
      run: |
        echo "## 📻 电台数据更新报告" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "✅ 数据更新完成！" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "**更新时间:** $(date)" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "**数据文件:**" >> $GITHUB_STEP_SUMMARY
        echo "- curated-stations.json" >> $GITHUB_STEP_SUMMARY
        echo "- asia-stations.json" >> $GITHUB_STEP_SUMMARY
        echo "- europe-stations.json" >> $GITHUB_STEP_SUMMARY
        echo "- americas-stations.json" >> $GITHUB_STEP_SUMMARY
        echo "- africa-stations.json" >> $GITHUB_STEP_SUMMARY
        echo "- oceania-stations.json" >> $GITHUB_STEP_SUMMARY
