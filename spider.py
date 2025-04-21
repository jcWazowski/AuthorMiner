import pandas as pd
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import logging
from datetime import datetime

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定义清理标题的函数，移除 and, or, not 关键词以及括号
def clean_title(title):
    """从标题中移除 and, or, not 等关键词以及括号及括号内容"""
    if pd.isna(title):
        return title
    
    # 使用正则表达式处理所有大小写形式的and, or, not
    import re
    
    # 替换所有形式的and, or, not (考虑到单词边界和前后空格)
    cleaned_title = title
    # 处理and及其变体
    cleaned_title = re.sub(r'\s+[Aa][Nn][Dd]\s+', ' ', cleaned_title)
    cleaned_title = re.sub(r'\s+[Aa][Nn][Dd]\.', '.', cleaned_title)
    # 处理or及其变体
    cleaned_title = re.sub(r'\s+[Oo][Rr]\s+', ' ', cleaned_title)
    cleaned_title = re.sub(r'\s+[Oo][Rr]\.', '.', cleaned_title)
    # 处理not及其变体
    cleaned_title = re.sub(r'\s+[Nn][Oo][Tt]\s+', ' ', cleaned_title)
    cleaned_title = re.sub(r'\s+[Nn][Oo][Tt]\.', '.', cleaned_title)
    
    # 移除括号及括号内容 - 处理嵌套括号情况
    cleaned_title = re.sub(r'\([^()]*\)', '', cleaned_title)
    # 处理可能留下的空格问题
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
    
    if cleaned_title != title:
        logger.info(f"标题已清理: '{title}' -> '{cleaned_title}'")
        
    return cleaned_title

# 定义随机延迟函数
def random_delay(min_seconds=1, max_seconds=3):
    """随机延迟一段时间，模拟人类行为"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay

# 初始化计数器
success_count = 0
fail_count = 0

# 1. 读取 Excel 文件
file_path = 'paper.xlsx'
df = pd.read_excel(file_path)
titles = df['论文题目']  # 使用新的列名获取论文标题
name_list = df['全部论文作者'].astype(str).tolist()  # 获取全部作者列表

# 添加一个新列用于保存通讯作者，插在全部论文作者和论文题目之间
if '通讯作者' not in df.columns:
    df.insert(2, '通讯作者', '')  # 插入在第三列位置

# 添加一个新列记录处理状态
df['处理状态'] = 'pending'

# 创建代理IP列表（如有需要，可以添加更多代理）
proxy_list = [
    # 格式: "ip:port"
    # 这里需要填入有效的代理IP，暂时留空
]

# 定义返回随机代理的函数
def get_random_proxy():
    if proxy_list:
        return random.choice(proxy_list)
    return None

# 定义一个函数来初始化浏览器，便于重试时创建新的浏览器实例
def init_browser():
    options = Options()
    
    # 使用随机User-Agent
    try:
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'user-agent={user_agent}')
        logger.info(f"使用User-Agent: {user_agent}")
    except:
        logger.warning("无法生成随机User-Agent，使用默认值")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # 随机设置浏览器窗口大小，避免被检测为自动化程序
    window_width = random.randint(1000, 1200)
    window_height = random.randint(800, 1000)
    options.add_argument(f"--window-size={window_width},{window_height}")
    
    # 添加随机代理（如果有代理列表）
    proxy = get_random_proxy()
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
        logger.info(f"使用代理: {proxy}")
    
    # 其他反检测选项
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 可选：使用无头模式，但有时无头模式更容易被检测到
    # options.add_argument("--headless")
    
    # 初始化浏览器
    driver = webdriver.Chrome(options=options)
    
    # 绕过webdriver检测
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": driver.execute_script("return navigator.userAgent").replace("Headless", "")
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # 设置等待
    wait = WebDriverWait(driver, 10)
    
    return driver, wait

# 定义检查和处理验证码的函数（假设存在这种情况）
def check_for_captcha(driver):
    try:
        # 这里需要根据目标网站的验证码特征进行修改
        captcha_element = driver.find_element(By.ID, 'captcha-container')
        if captcha_element.is_displayed():
            logger.warning("检测到验证码，暂停30秒等待手动处理")
            time.sleep(30)  # 给用户时间来解决验证码
            return True
    except:
        return False
    return False

# 定义搜索和提取通讯作者的函数
def process_article(driver, wait, title_idx, title, name_list):
    """处理单篇文章，每篇只尝试一次"""
    global success_count, fail_count
    
    base_url = 'https://webofscience.clarivate.cn/wos/woscc/advanced-search'
    
    try:
        logger.info(f"正在处理第 {title_idx + 1} 篇文章: '{title}'")
        
        # 检查是否有验证码
        if check_for_captcha(driver):
            logger.warning("检测到验证码，尝试处理后仍无法继续")
            fail_count += 1
            return False, ""
            
        # 3. 搜索文章标题
        logger.info("正在搜索标题...")
        search_box = wait.until(EC.presence_of_element_located((By.ID, 'advancedSearchInputArea')))
        search_box.clear()
        
        # 模拟人类输入行为
        title_to_search = 'TI=' + title
        for char in title_to_search:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.01, 0.1))  # 随机延迟模拟真人打字速度
            
        random_delay()
        
        # 处理可能的Cookie弹窗
        try:
            cookie_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            if cookie_button.is_displayed():
                cookie_button.click()
                random_delay()
        except:
            pass
        
        # 将搜索按钮滚动到视图中
        search_button = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'button[data-ta="run-search"]')
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
        random_delay()
        
        # 尝试点击
        search_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-ta="run-search"]')
        ))
        search_button.click()
        logger.info("已点击搜索按钮，等待加载结果...")
        random_delay(3, 5)
        
        # 等待搜索结果页面加载完成
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.title.title-link')))
            logger.info("搜索结果已加载，准备点击第一篇文章...")
        except:
            logger.warning("未找到搜索结果，可能没有匹配的文章")
            fail_count += 1
            return False, ""
            
        # 打开第一篇结果
        try:
            first_result = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a[data-ta="summary-record-title-link"]')
            ))
            first_result.click()
            logger.info("已点击第一篇文章，等待加载详情...")
            random_delay(3, 5)
        except:
            logger.warning("无法点击结果，尝试使用JavaScript点击")
            try:
                first_result = driver.find_element(By.CSS_SELECTOR, 'a[data-ta="summary-record-title-link"]')
                driver.execute_script("arguments[0].click();", first_result)
                random_delay(3, 5)
            except:
                fail_count += 1
                return False, ""
        
        # 4. 找到作者地址并提取通讯作者名字
        logger.info("开始查找通讯作者...")
        corr_authors = []
        
        try:
            # 首先找到author-info-section区域
            author_sections = driver.find_elements(By.CSS_SELECTOR, '.author-info-section.ng-star-inserted')
            logger.info(f"找到{len(author_sections)}个作者信息区域")
            
            for section in author_sections:
                # 查找所有通讯作者组
                addr_titles = section.find_elements(By.CSS_SELECTOR, '[id^="FRAiinTa-RepAddrTitle-"]')
                logger.info(f"找到{len(addr_titles)}组通讯作者信息")
                
                for addr_title in addr_titles:
                    # 对每组通讯作者，查找所有作者名
                    author_names = section.find_elements(By.CSS_SELECTOR, 'span.value.section-label-data')
                    for author_name in author_names:
                        name = author_name.text.strip()
                        if name:
                            if name in name_list:
                                name += '*'
                            corr_authors.append(name)
                            logger.info(f"找到通讯作者: {name}")
        except Exception as e:
            logger.error(f"查找通讯作者时出错: {e}")
            fail_count += 1
            return False, ""
            
        # 清洗通讯作者信息，使用分号和(corresponding author)作为分隔符
        cleaned_authors = []
        logger.info("开始清洗通讯作者信息...")
        
        # 将所有作者信息连接成一个字符串
        all_authors_text = '; '.join(corr_authors)
        logger.info(f"连接后的原始作者信息: {all_authors_text}")
        
        # 按照(corresponding author)拆分
        author_segments = all_authors_text.split('(corresponding author)')
        
        for segment in author_segments:
            # 按分号拆分
            names = segment.split(';')
            for name in names:
                name = name.strip()
                # 检查是否像一个人名 (通常是 "姓, 名" 格式)
                if ',' in name and len(name.split(',')) == 2:
                    last_name = name.split(',')[0].strip()
                    first_name = name.split(',')[1].strip()
                    # 确保姓和名都不为空且不含有明显的非人名信息
                    if (last_name and first_name and 
                        not any(x in name.lower() for x in ['univ', 'school', 'institute', 'dept'])):
                        cleaned_authors.append(name)
                        logger.info(f"提取到有效作者: {name}")
        
        # 去重
        cleaned_authors = list(dict.fromkeys(cleaned_authors))
        
        if cleaned_authors:
            logger.info(f"文章 {title_idx+1}: '{title}' 的通讯作者为: {', '.join(cleaned_authors)}")
            success_count += 1
            return True, '; '.join(cleaned_authors)
        else:
            logger.warning(f"未能提取到有效的通讯作者信息")
            fail_count += 1
            return False, ""
            
    except Exception as e:
        logger.error(f"处理第{title_idx + 1}篇文章时出错: {e}")
        fail_count += 1
        return False, ""

# 主处理函数，包含两轮尝试
def main_scraping_process(mode='skip_marked'):
    """
    爬取数据的主函数
    
    参数:
    mode: 可选值 'complete' 或 'skip_marked'
          'complete' - 重新检索并标记所有文章
          'skip_marked' - 跳过已有通讯作者的文章
    """
    global success_count, fail_count
    
    # 记录开始时间，用于计算总用时
    start_time = datetime.now()
    
    # 首先安装fake_useragent（如果尚未安装）
    try:
        import fake_useragent
    except ImportError:
        logger.info("正在安装fake_useragent...")
        import subprocess
        subprocess.call(['pip', 'install', 'fake-useragent'])
    
    logger.info(f"开始爬取数据... 模式: {mode}")
    logger.info(f"共有{len(titles)}篇文章需要处理")
    
    # 使用一个固定的输出文件名，而不是每次都创建新文件
    output_file = 'paper_with_authors_progress.xlsx'
    update_interval = 5  # 每处理5篇文章更新一次文件
    
    # 用于记录失败的文章序号
    failed_article_indexes = []
    
    # 初始化浏览器
    driver, wait = init_browser()
    
    base_url = 'https://webofscience.clarivate.cn/wos/woscc/advanced-search'
    driver.get(base_url)
    random_delay(2, 4)
    
    # 处理初始Cookie弹窗
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        logger.info("检测到 Cookie 弹窗，尝试关闭...")
        accept_button.click()
        random_delay()
    except:
        logger.info("未检测到 Cookie 弹窗，继续执行...")
    
    # 第一轮：处理所有文章
    processed_count = 0
    for idx, title in enumerate(titles):
        # 检查是否跳过已标记文章
        if mode == 'skip_marked' and (
            # 检查作者字段中是否包含*号，表示已经标记过通讯作者
            ('*' in str(df.at[idx, '全部论文作者'])) or 
            # 同时也保留原来的检查，确保兼容性
            (not pd.isna(df.at[idx, '通讯作者']) and df.at[idx, '通讯作者'].strip() != '')
        ):
            logger.info(f"跳过第 {idx+1} 篇文章，已有通讯作者标记")
            df.at[idx, '处理状态'] = '已标记'  # 修改处理状态为"已标记"
            processed_count += 1
            # 计入已处理文章，并保存进度
            if processed_count % update_interval == 0:
                df.to_excel(output_file, index=False)
            continue
            
        if pd.isna(title):
            logger.info(f"跳过第 {idx+1} 篇文章，标题为空")
            df.at[idx, '处理状态'] = 'skip'
            continue
        
        # 清理标题，移除 and, or, not 等关键词以及括号
        cleaned_title = clean_title(title)
        
        success, corr_authors = process_article(driver, wait, idx, cleaned_title, name_list)
        
        if success:
            df.at[idx, '通讯作者'] = corr_authors
            df.at[idx, '处理状态'] = 'success'
        else:
            df.at[idx, '处理状态'] = 'failed_round1'
            # 记录第一轮失败的文章序号
            failed_article_indexes.append(idx + 1)
        
        processed_count += 1
        
        # 定期保存进度（每处理update_interval篇文章或处理到最后一篇时）
        if processed_count % update_interval == 0 or idx == len(titles) - 1:
            df.to_excel(output_file, index=False)
        
        # 返回主页准备下一个搜索
        driver.get(base_url)
        random_delay(2, 5)
    
    # 重启浏览器，避免长时间运行导致的问题
    driver.quit()
    random_delay(5, 10)
    driver, wait = init_browser()
    driver.get(base_url)
    random_delay(2, 4)
    
    # 处理Cookie弹窗
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_button.click()
        random_delay()
    except:
        pass
    
    # 第二轮：重试第一轮失败的文章
    failed_indices = df[df['处理状态'] == 'failed_round1'].index.tolist()
    
    # 清空失败文章索引列表，以便记录第二轮仍然失败的文章
    failed_article_indexes = []
    
    processed_count = 0
    for idx in failed_indices:
        title = titles[idx]
        
        # 清理标题，移除 and, or, not 等关键词以及括号
        cleaned_title = clean_title(title)
        
        success, corr_authors = process_article(driver, wait, idx, cleaned_title, name_list)
        
        if success:
            df.at[idx, '通讯作者'] = corr_authors
            df.at[idx, '处理状态'] = 'success'
        else:
            df.at[idx, '处理状态'] = 'failed'
            # 记录最终失败的文章序号
            failed_article_indexes.append(idx + 1)  # +1 转换为从1开始的序号
        
        processed_count += 1
        
        # 定期保存进度
        if processed_count % update_interval == 0 or idx == failed_indices[-1]:
            df.to_excel(output_file, index=False)
        
        # 返回主页准备下一个搜索
        driver.get(base_url)
        random_delay(2, 5)
    
    # 关闭浏览器
    driver.quit()
    
    # 计算总用时
    end_time = datetime.now()
    total_time = end_time - start_time
    hours, remainder = divmod(total_time.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # 统计结果
    success_count = len(df[df['处理状态'] == 'success'])
    fail_count = len(df[df['处理状态'] == 'failed'])
    skip_count = len(df[df['处理状态'] == 'skip'])
    marked_count = len(df[df['处理状态'] == '已标记'])
    
    # 只记录简要统计信息
    logger.info("\n========== 爬取结果摘要 ==========")
    logger.info(f"总篇数: {len(titles)}")
    logger.info(f"成功处理: {success_count} 篇")
    logger.info(f"处理失败: {fail_count} 篇")
    logger.info(f"已标记跳过: {marked_count} 篇")
    if failed_article_indexes:
        logger.info(f"失败文章序号: {', '.join(map(str, failed_article_indexes))}")
    logger.info(f"总用时: {int(hours)}小时{int(minutes)}分{int(seconds)}秒")
    
    return df, failed_article_indexes, total_time

# 主程序入口
if __name__ == "__main__":
    import argparse
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='Web of Science论文通讯作者爬虫')
    parser.add_argument('--mode', type=str, choices=['complete', 'skip_marked'], default='skip_marked',
                      help='爬取模式: complete-重新处理所有文章, skip_marked-跳过已有通讯作者的文章 (默认: skip_marked)')
    
    # 解析命令行参数
    args = parser.parse_args()
    logger.info(f"选择的爬取模式: {args.mode}")
    
    try:
        # 执行主要爬取过程，传入模式参数
        df, failed_article_indexes, total_time = main_scraping_process(args.mode)
        
        # 6. 保存结果到Excel文件
        output_file = 'paper_with_authors_final.xlsx'
        df.to_excel(output_file, index=False)
        
        # 打印最终统计
        print("\n========== 爬取任务完成 ==========")
        print(f"总文章数: {len(df)}")
        print(f"成功处理: {success_count} 篇")
        print(f"处理失败: {fail_count} 篇")
        if failed_article_indexes:
            print(f"失败文章序号: {', '.join(map(str, failed_article_indexes))}")
        print(f"总用时: {total_time}")
        
    except Exception as e:
        logger.error(f"程序执行过程中发生错误: {e}")
        print(f"程序执行过程中发生错误: {e}")
