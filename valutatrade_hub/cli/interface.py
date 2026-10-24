import shlex

from valutatrade_hub.core.usecases import login, register


def main():
    current_user = None

    while True:
        user_input = input("Введите команду: ")

        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Некорректное значение: незакрытая кавычка. Попробуйте снова.")
            continue

        if len(args) < 1:
            print("Неизвестная команда. Попробуйте снова.")
            continue

        match args[0]:
            case "register":
                if len(args) != 5 or args[1] != "--username" or args[3] != "--password":
                    print("Некорректный формат. Попробуйте снова.")
                    continue

                try:
                    user = register(args[2], args[4])
                except ValueError as e:
                    print(e)
                    continue

                print(
                    f"Пользователь '{user.username}' зарегистрирован "
                    f"(id={user.user_id}). "
                    f"Войдите: login --username {user.username} --password ****"
                )
            case "login":
                if len(args) != 5 or args[1] != "--username" or args[3] != "--password":
                    print("Некорректный формат. Попробуйте снова.")
                    continue

                try:
                    current_user = login(args[2], args[4])
                except ValueError as e:
                    print(e)
                    continue

                print(f"Вы вошли как '{current_user.username}'")
            case "show-portfolio":
                ...
            case "exit":
                break
            case _:
                print("Неизвестная команда.")


if __name__ == "__main__":
    main()
