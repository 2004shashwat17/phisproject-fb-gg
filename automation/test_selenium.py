from automation.browser_automation import BrowserAutomation

if __name__ == '__main__':
    print('starting headless browser test on Facebook')
    bot = BrowserAutomation(headless=True)
    bot.start()
    # go to Facebook login page
    bot.navigate('https://www.facebook.com/login')
    print('title:', bot.driver.title)
    # take screenshot and maybe enter credentials or just check presence of form
    bot.save_screenshot('facebook.png')
    bot.close()
    print('done')
