import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# 设置Chrome选项
chrome_options = Options()
chrome_options.add_argument("--headless")  # 不显示浏览器
chrome_options.add_argument("--disable-gpu")

# 使用webdriver-manager自动管理ChromeDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def login_sim_companies(email, password):
    """使用Selenium模拟登录Sim Companies网站"""
    try:
        driver.get("https://www.simcompanies.com/signin/")
        wait = WebDriverWait(driver, 20)  # 设置显式等待

        email_field = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="email"]')))
        password_field = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="password"]')))

        email_field.send_keys(email)
        password_field.send_keys(password)

        password_field.send_keys(Keys.RETURN)
        time.sleep(10)  # 等待登录完成

        cookies = driver.get_cookies()
        session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
        print("登录成功，已获取cookies！")
        return session_cookies
    except Exception as e:
        print(f"登录时出现问题: {e}")
        print("Page Source:", driver.page_source)  # 打印页面源码
        return None

def fetch_api_data(api_url, cookies):
    """使用获取到的Cookies访问受保护的API"""
    try:
        response = requests.get(api_url, cookies=cookies)
        if response.status_code == 200:
            print("API数据获取成功！")
            return response.json()  # 返回API响应的JSON数据
        else:
            print(f"API请求失败，状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"请求出现异常: {e}")
    return None

def make_hashable(obj):
    """递归将对象转换为可哈希类型（用于去重）"""
    if isinstance(obj, (set, list)):
        return tuple(make_hashable(e) for e in obj)
    elif isinstance(obj, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
    return obj

def save_data(data, save_path):
    """将数据保存到指定路径（去掉重复的部分，使用UTF-8编码）"""
    try:
        # 如果文件已存在，则先读取已有的数据并合并
        if os.path.exists(save_path):
            with open(save_path, 'r', encoding='utf-8') as file:
                existing_data = [eval(line) for line in file.read().splitlines()]  # 反序列化为字典列表
        else:
            existing_data = []

        # 合并并去重
        all_data = existing_data + data
        # 去重：递归处理嵌套的字典并转换为可哈希的类型
        unique_data = list({make_hashable(d): d for d in all_data}.values())

        # 保存去重后的数据
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write("\n".join([str(item) for item in unique_data]) + "\n")

    except UnicodeEncodeError as e:
        print(f"编码错误：{e}。尝试处理数据中的非法字符...")
        with open(save_path, 'w', encoding='utf-8', errors='replace') as file:
            file.write("\n".join([str(item) for item in unique_data]) + "\n")

def log_action(log_file, message):
    """保存日志记录"""
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# 用户输入
email = input("请输入你的用户名: ")
password = input("请输入你的密码: ")

# API选项
api_urls = {
    "ZH": "https://www.simcompanies.com/api/chatroom/?chatroom=N&last_id=1000000000",
    "EN": "https://www.simcompanies.com/api/chatroom/?chatroom=G&last_id=1000000000",
    "R2_H": "https://www.simcompanies.com/api/chatroom/?chatroom=H&last_id=1000000000",
    "R2_X": "https://www.simcompanies.com/api/chatroom/?chatroom=X&last_id=1000000000",
}

# 显示API选项并让用户选择
print("请选择要提取数据的API（用逗号分隔多个选项，或输入'all'选择全部）：")
for key in api_urls.keys():
    print(f"{key}: {api_urls[key]}")
user_selection = input("输入你的选择: ").strip()

if user_selection.lower() == 'all':
    selected_api_keys = list(api_urls.keys())
else:
    selected_api_keys = [key.strip() for key in user_selection.split(',') if key.strip() in api_urls]

# 确保有选择的API
if not selected_api_keys:
    print("没有有效的API选择，程序结束。")
    driver.quit()
    exit()

# 获取保存文件位置和保存频率
save_location = input("请输入保存文件的目录路径（例如：C:/data/）：").rstrip('/') + '/'
log_location = os.path.join(save_location, "log.txt")  # 保存日志文件的位置
interval = int(input("请输入提取时间间隔（秒）: "))
iterations = int(input("请输入提取次数（0表示无限提取）: "))
save_interval = int(input("请输入保存的提取次数间隔: "))  # 用户输入保存的提取次数间隔

# 使用Selenium模拟登录
cookies = login_sim_companies(email, password)

# 初始化缓冲区用于合并数据
all_data_buffer = {key: [] for key in selected_api_keys}

# 修改保存数据的逻辑
if cookies:
    try:
        count = 0  # 记录提取次数
        save_count = 0  # 记录当前提取周期内的保存计数

        while True:
            for api_key in selected_api_keys:
                api_url = api_urls[api_key]
                data = fetch_api_data(api_url, cookies)
                if data:
                    print(f"获取到的数据 ({api_key}):", data)
                    all_data_buffer[api_key].extend(data)  # 将数据加入缓冲区

            save_count += 1  # 增加保存计数

            # 每提取save_interval次保存一次
            if save_count >= save_interval:
                timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
                for api_key in selected_api_keys:
                    data = all_data_buffer[api_key]
                    if data:  # 如果缓冲区有数据
                        # 去重并保存数据
                        unique_data = list({make_hashable(d): d for d in data}.values())
                        save_path = os.path.join(save_location, f"{api_key}_{timestamp}.txt")  # 保存文件名带有时间戳
                        save_data(unique_data, save_path)  # 保存并去重
                        log_action(log_location, f"已保存数据到 {save_path}")  # 记录日志
                        print(f"已保存数据到 {save_path}")
                        all_data_buffer[api_key] = []  # 清空缓冲区

                save_count = 0  # 重置保存计数

            count += 1
            if iterations > 0 and count >= iterations:
                break

            print(f"等待 {interval} 秒后进行下一次提取...")
            time.sleep(interval)  # 等待指定的时间


    except KeyboardInterrupt:
        print("提取过程被中断。")
    finally:
        # 在关闭程序之前保存当前缓冲区数据
        if any(all_data_buffer.values()):  # 检查是否有未保存的数据
            timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            for api_key, data in all_data_buffer.items():
                if data:
                    save_path = os.path.join(save_location, f"{api_key}_{timestamp}.txt")
                    save_data(data, save_path)
                    log_action(log_location, f"程序终止前已保存数据到 {save_path}")
                    print(f"程序终止前已保存数据到 {save_path}")

        driver.quit()
