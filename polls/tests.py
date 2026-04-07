from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from django.contrib.auth.models import User
import time

class MySeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--width=1920')
        opts.add_argument('--height=1080')
        cls.selenium = webdriver.Firefox(options=opts)
        cls.selenium.implicitly_wait(10)
        
        # Creem superusuari segons l'estratègia del document [cite: 35, 47-51]
        user = User.objects.create_user("isard", "isard@isardvdi.com", "pirineus")
        user.is_superuser = True
        user.is_staff = True
        user.save()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_staff_permissions(self):
        # 1. Login
        self.selenium.get(f"{self.live_server_url}/admin/")
        self.selenium.find_element(By.NAME, "username").send_keys("isard")
        self.selenium.find_element(By.NAME, "password").send_keys("pirineus")
        self.selenium.find_element(By.XPATH, "//input[@type='submit']").click()

        # 2. Crear usuari staff (operació de Selenium simulant usuari extern) [cite: 53-54]
        self.selenium.find_element(By.XPATH, "//a[@href='/admin/auth/user/add/']").click()
        self.selenium.find_element(By.NAME, "username").send_keys("staff_user")
        pwds = self.selenium.find_elements(By.XPATH, "//input[@type='password']")
        pwds[0].send_keys("PassEAC2_2026!")
        pwds[1].send_keys("PassEAC2_2026!")
        self.selenium.find_element(By.NAME, "_save").click()

        # 3. Editar l'usuari creat
        self.selenium.find_element(By.XPATH, "//a[text()='staff_user']").click()
        
        # --- SOLUCIÓ AL MOVE OUT OF BOUNDS ---
        # Forcem el scroll fins a la secció de permisos usant JS
        is_staff = self.selenium.find_element(By.NAME, "is_staff")
        self.selenium.execute_script("arguments[0].scrollIntoView();", is_staff)
        time.sleep(1) 
        is_staff.click()

        # 4. Assignar permisos (Doble clic)
        # Scroll fins a la caixa de permisos
        opt_add = self.selenium.find_element(By.XPATH, "//select[@id='id_user_permissions_from']/option[contains(text(), 'Can add user')]")
        self.selenium.execute_script("arguments[0].scrollIntoView();", opt_add)
        ActionChains(self.selenium).double_click(opt_add).perform()

        opt_view = self.selenium.find_element(By.XPATH, "//select[@id='id_user_permissions_from']/option[contains(text(), 'Can view user')]")
        self.selenium.execute_script("arguments[0].scrollIntoView();", opt_view)
        ActionChains(self.selenium).double_click(opt_view).perform()

        # 5. Guardar i Logout
        save_btn = self.selenium.find_element(By.NAME, "_save")
        self.selenium.execute_script("arguments[0].scrollIntoView();", save_btn)
        save_btn.click()
        
        self.selenium.find_element(By.XPATH, "//button[text()='Log out'] | //a[contains(text(),'Log out')]").click()

        # 6. Login amb Staff i comprovacions [cite: 56]
        self.selenium.get(f"{self.live_server_url}/admin/")
        self.selenium.find_element(By.NAME, "username").send_keys("staff_user")
        self.selenium.find_element(By.NAME, "password").send_keys("PassEAC2_2026!")
        self.selenium.find_element(By.XPATH, "//input[@type='submit']").click()

        # Comprovar que SÍ pot crear usuaris [cite: 58-59]
        self.selenium.find_element(By.XPATH, "//a[@href='/admin/auth/user/add/']")

        # Comprovar que NO pot crear preguntes (estratègia try/except del document) [cite: 61-70]
        try:
            self.selenium.find_element(By.XPATH, "//a[@href='/admin/polls/question/add/']")
            assert False, "Error: El staff NO hauria de poder crear Questions"
        except NoSuchElementException:
            pass # Èxit: l'element no hi és
