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

def save_data(data, save_path):
    """将数据保存到指定路径"""
    with open(save_path, 'a') as file:
        file.write(f"{data}\n")  # 将数据以换行方式写入文件

def log_action(log_file, message):
    """保存日志记录"""
    with open(log_file, 'a') as log:
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

# 如果登录成功，使用获取到的cookies访问API
if cookies:
    try:
        count = 0  # 记录提取次数
        save_count = 0  # 记录当前提取周期内的保存计数

        while True:
            all_data = {}  # 保存每个API提取到的数据
            for api_key in selected_api_keys:
                api_url = api_urls[api_key]
                data = fetch_api_data(api_url, cookies)
                if data:
                    print(f"获取到的数据 ({api_key}):", data)
                    all_data[api_key] = data
                    save_count += 1  # 增加保存计数

            # 每提取save_interval次保存一次
            if save_count >= save_interval or (iterations > 0 and count >= iterations):
                timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
                for api_key, data in all_data.items():
                    save_path = os.path.join(save_location, f"{api_key}_{timestamp}.txt")  # 保存文件名带有时间戳
                    save_data(data, save_path)
                    log_action(log_location, f"已保存数据到 {save_path}")  # 记录日志
                    print(f"已保存数据到 {save_path}")

                save_count = 0  # 重置保存计数

            count += 1
            if iterations > 0 and count >= iterations:
                break

            print(f"等待 {interval} 秒后进行下一次提取...")
            time.sleep(interval)  # 等待指定的时间

    except KeyboardInterrupt:
        print("提取过程被中断。")
    finally:
        # 在关闭程序之前保存数据
        if save_count > 0:
            timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            for api_key, data in all_data.items():
                save_path = os.path.join(save_location, f"{api_key}_{timestamp}.txt")  # 保存文件名带有时间戳
                save_data(data, save_path)
                log_action(log_location, f"程序终止前已保存数据到 {save_path}")
                print(f"程序终止前已保存数据到 {save_path}")

        # 关闭浏览器
        driver.quit()
