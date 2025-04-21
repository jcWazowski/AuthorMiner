# AuthorMiner - Web of Science Corresponding Author Extractor

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/selenium-4.1.0+-green.svg)](https://www.selenium.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub stars](https://img.shields.io/github/stars/jcWazowski/AuthorMiner?style=social)

**An ethical data extraction tool for academic research purposes only**  
**仅供学术研究使用的合规数据采集工具**

---

## 🔍 Intellectual Property Notice / 知识产权声明
❗ **Important Legal Notice** ❗  
Web of Science data is protected by copyright and terms of service. This tool:
- Extracts ONLY corresponding author information (minimal necessary data)
- MUST be used in compliance with WOS Terms of Service
- Requires legitimate institutional access
- Is not affiliated with Clarivate Analytics

❗ **重要法律声明** ❗  
Web of Science数据受版权和服务条款保护。本工具：
- 仅提取通讯作者信息（最小必要数据）
- 必须遵守WOS服务条款使用
- 需要合法的机构访问权限
- 与Clarivate Analytics无隶属关系

---

## ✨ Features / 功能特点
### Core Functionality / 核心功能
- 📥 Suitable for paper list directly export from Web of Science which contains author list without marking corresponding author 

    适用于从Web of Science导出的文献列表，包含了作者信息但没有对通讯作者标记
- 🔍 Automatically searches Web of Science for detailed information  
  自动搜索Web of Science获取详细信息
- ⭐ Extracts and marks corresponding authors with asterisks *
  提取通讯作者信息并用星号*标记


### Advanced Capabilities / 高级功能
- 🧠 Intelligent title filtering (handles variations of "and", "or", "not" regardless of case)  
  智能过滤标题中的关键词和括号内容
- 💾 Auto-saves progress with resume capability  
  支持断点续爬，定期保存进度
- 🤖 Automatic handling of cookie popups  
  自动应对Cookie弹窗
- 📝 Detailed logging for troubleshooting  
  详细的日志记录

### Output Management / 输出管理
- 🗂️ Generates multiple output files with clear progress tracking  
  生成多个输出文件，进度清晰可查

---

## 🛠️ Installation / 安装方法

### Prerequisites / 前提条件
- Python 3.7+
- Chrome browser
- ChromeDriver (matching your Chrome version)

### Installation Steps / 安装步骤
1. Clone the repository:
```bash
git clone https://github.com/jcWazowski/AuthorMiner.git
cd AuthorMiner
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure ChromeDriver is in PATH or place `chromedriver.exe` in the root directory.

    if you do not, visit https://googlechromelabs.github.io/chrome-for-testing/
---

## 🚀 Usage / 使用方法

### Input Preparation / 准备输入文件
Prepare an Excel file named `paper.xlsx` containing:
- 论文题目Paper Title (complete title)
- 全部论文作者All Authors (names separated by semicolons)

Currently we only detect by Chinese, replace the key word in function *mark_corresponding_authors* in *mark.py* if you need to

See example_input.xlsx and example_output.xlsx if you don't know how to organize your file
### Running the Crawler / 运行爬虫
#### Skip Marked Articles (Default Mode)
```bash
python spider.py
# or explicitly
python spider.py --mode skip_marked
```

#### Process All Articles (Complete Mode)
```bash
python spider.py --mode complete
```

### Post-Processing / 处理结果
```bash
python mark.py
```

---

## 📂 Output Files / 输出文件
| File Name | Description |
|-----------|-------------|
| `paper_with_authors_progress.xlsx` | Interim progress file |
| `paper_with_authors_final.xlsx` | Final crawled results |
| `paper_with_authors_updated.xlsx` | Marked final output |
| `scraper_log.txt` | Detailed operation log |

---

## 📜 License & Compliance / 许可证与合规
**MIT License** with additional terms:
1. User assumes ALL legal responsibility
2. Must have legal WOS access

**附加条款**:
1. 使用者承担全部法律责任
2. 必须拥有合法WOS访问权限

