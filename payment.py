#! /usr/bin/env python3
from selenium import webdriver
import pyperclip, sys, os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image
import argparse
from datetime import datetime

def getPositionCode(area, buildingName, unit, roomNum):
	direction = buildingName[0]
	buildingNum = buildingName[1:]

	directions = {'东': 'E', '西': 'W'}
	numbers = {'一': '01', '二': '02', '三': '03', '四': '04', '五': '05', 
	'六': '06', '九': '09', '十': '10', '十二': '12', '十三': '13', 
	'十四': '14', '十五': '15', '十六': '16', '十九': '19'}
	if direction == '东' or direction == '西':
		position = '{}{}{}'.format(buildingName, unit, roomNum)
		code = directions[direction]
		code += numbers[buildingNum]
	else:
		special = {'星河楼': 'XHL', '陶南': 'TTN', '陶北': 'TTB', '沁园': 'TQY', '研究生公寓': 'YGY'}
		code = special[buildingName]
		position = '{}{}'.format(buildingName, roomNum)

	positionCode = '{}{}{}'.format(area, code, roomNum)
	return position, positionCode
	

# set basic info
shipai = '01'
unit = '栋'
url = 'http://pay.scnu.edu.cn/pay.html'
filename = 'QRcode.png'
desktopPath = os.path.expanduser('~/Desktop')
pathOfScreenShot = os.path.join(desktopPath, filename)

# get the current year and month
now = datetime.now()
year = now.year
month = now.month
# set argument options
parser = argparse.ArgumentParser(description='Simple app to pay for overheads in SCNU(tianhe, Guangzhou)')
parser.add_argument('-p', '--position', default='西三', choices={'西一', '西二', '西三', '西四', '西五', '西六', 
	'东四', '东九', '东十', '东十二', '东十三', '东十四', '东十五', '东十六', '东十九', '星河楼', '陶南', '陶北', 
	'沁园', '研究生公寓'}, help='Specify the position of your dormitory', action='store', dest='position')
parser.add_argument('-n', '--number', default='401', help='Specify the room number', metavar='{room number}', action='store', dest='number')
args = parser.parse_args()
# extract args 
roomNum = args.number
buildingName = args.position

# generate id number
position, positionCode = getPositionCode(shipai, buildingName, unit, roomNum)
myID = '{}{:02d}{}'.format(year, month, positionCode)
# display basic info
previous = (month-1) % 12
if previous == 0:
	previous = 12
print('---{}月电费---'.format(previous))
print('网址: {}\n人员编号: {}\n宿舍: {}'.format(url, myID, position))

# headless browser
options = Options()
options.add_argument("headless");
options.add_argument("window-size=1200x600");
browser = webdriver.Chrome(chrome_options=options)

# get state of payment
try:
	# send request
	browser.get(url)
	idInput = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="userId"]'))
	)
	nameInput = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="userName"]'))
	)
	searchButton = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="queryPayCodeBtn"]'))
	)

	idInput.clear()
	idInput.send_keys(myID)
	nameInput.clear()
	nameInput.send_keys(position)
	searchButton.click()

	statusElem = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="payCodeDiv"]/table/tbody/tr[3]/td[5]'))
	)
	payCodeElem = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="payCodeDiv"]/table/tbody/tr[3]/td[4]/a'))
	)
	payCodeInputBox = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="pwd"]'))
	)
	confirmPayCodeBtn = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="payForm"]/table/tbody/tr[5]/td/input'))
	)
	status = statusElem.text
	print('='*16)
	print('支付情况: {}'.format(status))
	print('='*16)
	if status == '已支付':
		browser.quit()
		sys.exit()
	else:
		# get payment code
		payCode = payCodeElem.text
		print('支付码: {}'.format(payCode))

		# copy to clipboard
		pyperclip.copy(payCode)
		print("===Pay code successful copied to clipboard!===")

		# input paycode
		payCodeInputBox.clear()
		payCodeInputBox.send_keys(payCode);
		# confirm paycode
		confirmPayCodeBtn.click()
		# switch to payment page
		browser.switch_to_window(browser.window_handles[-1])
except TimeoutException:
	print("===无效宿舍号!(或 无网络连接)===")
	browser.quit()
	sys.exit()

# check amount of money to pay and choose Wechat 
try:
	amount = WebDriverWait(browser, 5).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="print_pay"]/table/tbody/tr[6]/td[2]/strong'))
	)
	print('金额: {} 元'.format(amount.text))

	wechatOption = WebDriverWait(browser, 5).until(
		EC.element_to_be_clickable((By.ID, 'bank1'))
	)

	payAllBtn = WebDriverWait(browser, 5).until(
		EC.element_to_be_clickable((By.XPATH, '//*[@id="payInfoForm"]/center/div[1]/input'))
	)

	wechatOption.click()
	payAllBtn.click()
except TimeoutException:
	print('支付信息获取失败!')
	browser.quit()
	sys.exit()


# load QR code and save the screenshot on the desktop
try:
	frame = WebDriverWait(browser, 5).until(
		EC.frame_to_be_available_and_switch_to_it((By.NAME, "iframe"))
	)
	qrCodeLoaded = WebDriverWait(browser, 5).until(
		EC.presence_of_element_located((By.CSS_SELECTOR, 'img[src^="/create"]'))
	)
	browser.save_screenshot(pathOfScreenShot)
	print('Scan QR code!')
	img = Image.open(pathOfScreenShot)
	img.show()
except TimeoutException:
	print('目前是银行结算时间，请在每天的03：30~22：00时间段内进行交费，谢谢合作。')
finally:
	browser.quit()
