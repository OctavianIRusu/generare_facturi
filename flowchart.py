from pyflowchart import Flowchart
code = """def main(self):
        print("-" * 65)
        print("Bine ai venit! Pentru a continua este necesara autentificarea!")
        while True:
            print("-" * 65)
            username = input("Introduceti numele de utilizator: ")
            password = input("Introduceti parola: ")
            time.sleep(0.75)

            authenticated, self.is_admin = authenticate(username, password, self.cursor)
            print("-" * 65)

            if authenticated:
                print("Salut, {}! Ai fost autentificat/a ca {}."
                        .format(username, 'administrator' if self.is_admin else 'user'))
                self.username = username

                if self.is_admin:
                    self.handle_admin_menu()
                else:
                    self.handle_user_menu()
                break
            else:
                raise AuthenticationError("Username sau parola gresita!")"""
                    
fc = Flowchart.from_code(code)

with open ('flowchart.txt', 'w') as f:
    f.write(fc.flowchart())