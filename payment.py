#! /usr/bin/env python3
from selenium import webdriver
import sys, os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from PIL import Image
import argparse

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
url = 'https://ssp.scnu.edu.cn/pay/opt_wyjf.aspx'

# default args
defaultRoom = 401
defaultBuilding = '西三'

# set argument options
parser = argparse.ArgumentParser(description='Simple app to pay for overheads in SCNU(tianhe, Guangzhou)')
parser.add_argument('-p', '--position', default=defaultBuilding, choices={'西一', '西二', '西三', '西四', '西五', '西六', 
	'东四', '东九', '东十', '东十二', '东十三', '东十四', '东十五', '东十六', '东十九', '星河楼', '陶南', '陶北', 
	'沁园', '研究生公寓'}, help='Specify the position of your dormitory', action='store', dest='position')
parser.add_argument('-n', '--number', default=defaultRoom, help='Specify the room number', metavar='{room number}', action='store', dest='number')
args = parser.parse_args()
# extract args 
roomNum = args.number
buildingName = args.position

# generate position code
position, positionCode = getPositionCode(shipai, buildingName, unit, roomNum)
# display basic info
print('网址: {}\n宿舍编号: {}\n宿舍: {}'.format(url, positionCode, position))

# get state of payment
try:
	# headless browser
	options = Options()
	options.add_argument("headless")
	options.add_argument("window-size=1200x600")
	browser = webdriver.Chrome(chrome_options=options)
	# send request
	browser.get(url)
	idInput = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="pn_ssh"]'))
	)
	searchButton = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="pn_sc"]'))
	)
	idInput.clear()
	idInput.send_keys(positionCode)
	# send search request
	searchButton.click()

	yearElem = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="gv1"]/tbody/tr[2]/td[4]'))
	)

	monthElem = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="gv1"]/tbody/tr[2]/td[5]'))
	)

	overheadsElem = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="gv1"]/tbody/tr[2]/td[7]'))
	)

	payBtnElem = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="gv1"]/tbody/tr[2]/td[1]/a'))
	)

	payStatus = WebDriverWait(browser, 3).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="gv1"]/tbody/tr[2]/td[10]/span/input'))
	)
	
	year = yearElem.text
	month = monthElem.text
	overheads = overheadsElem.text
	# check need for paying
	status = payStatus.get_attribute('checked')
	
	print('='*16)
	print('{}年{}月 电费'.format(year, month))
	print('='*16)
	print('总金额: {} 元'.format(overheads))

	# show the status of payment
	if status != None:
		print('支付情况: 已支付')
		browser.quit()
		sys.exit()
		
	# forward to payment page
	payBtnElem.click()

except TimeoutException:
	print("===无支付信息, 请检查宿舍号和网络连接===")
	browser.quit()
	sys.exit()
except WebDriverException:
	print("请安装Google Chrome浏览器!")
	sys.exit()

# choose Wechat option
try:
	wechatOption = WebDriverWait(browser, 5).until(
		EC.element_to_be_clickable((By.ID, 'bank1'))
	)

	payAllBtn = WebDriverWait(browser, 5).until(
		EC.element_to_be_clickable((By.XPATH, '//*[@id="payInfoForm"]/center/div[1]/input'))
	)

	wechatOption.click()
	payAllBtn.click()
except TimeoutException:
	print('支付情况: 已支付')
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
	# construct the path to save the screenshot
	desktopPath = os.path.expanduser('~/Desktop')
	filename = '{}.{}-{}.png'.format(year, month, position)
	pathOfScreenShot = os.path.join(desktopPath, filename)
	browser.save_screenshot(pathOfScreenShot)
	
	print('请扫描二维码!')
	# open the image
	img = Image.open(pathOfScreenShot)
	img.show()
except TimeoutException:
	print('目前是银行结算时间，请在每天的03：30~22：00时间段内进行交费，谢谢合作。')
finally:
	browser.quit()
