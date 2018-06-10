#! /usr/bin/env python3
from selenium import webdriver
import pyperclip, sys, os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image
import argparse
from datetime import datetime

def getPositionCode(position):
	direction = position[0]
	number = position[1:]

	directions = {'东': 'E', '西': 'W'}
	west = {'一': '01', '二': '02', '三': '03', '四': '04', '五': '05', '六': '06'}
	east = {'四': '04', '九': '09', '十': '10', '十二': '12', '十三': '13', '十四': '14', '十五': '15', '十六': '16', '十九': '19'}
	if direction == '东':
		code = directions[direction]
		code += east[number]
	elif direction == '西':
		code = directions[direction]
		code += west[number]
	else:
		special = {'星河楼': 'XHL', '陶南': 'TTN', '陶北': 'TTB', '沁园': 'TQY', '研究生公寓': 'YGY'}
		code = special[position]
	return code

# set basic info
shipai = '01'
unit = '栋'
url = 'http://pay.scnu.edu.cn/pay.html'
filename = 'QRcode.png'
desktopPath = os.path.expanduser('~/Desktop')
pathOfScreenShot = os.path.join(desktopPath, filename)

# get the current year
now = datetime.now()
yearCurrent = now.year
# set argument options
parser = argparse.ArgumentParser(description='Simple app to pay for overheads in SCNU(tianhe, Guangzhou)')
parser.add_argument('-y', '--year', required=True, choices=range(yearCurrent-1, yearCurrent+1), type=int, help='Specify the year', action='store', dest='year')
parser.add_argument('-m', '--month', required=True, choices=range(1, 13), type=int, help='Specify the month', action='store', dest='month')
parser.add_argument('-p', '--position', required=True, choices={'西一', '西二', '西三', '西四', '西五', '西六', 
	'东四', '东九', '东十', '东十二', '东十三', '东十四', '东十五', '东十六', '东十九', '星河楼', '陶南', '陶北', 
	'沁园', '研究生公寓'}, help='Specify the position of your dormitory', action='store', dest='position')
parser.add_argument('-n', '--number', required=True, help='Specify the room number', action='store', dest='number')
args = parser.parse_args()
# extract args 
year = args.year
month = args.month
roomNum = args.number

# generate id number
position = '{}{}{}'.format(args.position, unit, roomNum)
positionCode = '{}{}{}'.format(shipai, getPositionCode(args.position), roomNum)
myID = '{}{:02d}{}'.format(year, month, positionCode)
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
	print('支付情况: {}'.format(status))
	if status == '已支付':
		print("\n===You've paid for it!===\nSee you!")
		browser.quit()
		sys.exit()
	else:
		print("\n===You have to pay for it!===\n")
		# get payment code
		payCode = payCodeElem.text
		print('Pay code: {}'.format(payCode))

		# copy to clipboard
		pyperclip.copy(payCode)
		print("===Pay code successful copied to clipboard!===")

		# input paycode
		payCodeInputBox.clear()
		payCodeInputBox.send_keys(payCode);
		# confirm paycode
		confirmPayCodeBtn.click()

		browser.switch_to_window(browser.window_handles[-1])
except Exception:
	print("===无效月份!(或 网络连接失败)===")
	browser.quit()
	sys.exit()



# check amount of money to pay and choose wechat 
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
except Exception:
	print('No payment info!')
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
finally:
    browser.quit()
