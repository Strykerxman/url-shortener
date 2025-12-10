from config import get_settings

def main():
    settings = get_settings()
    print("Debug Mode:", settings.debug)
    print("Base URL:", settings.base_url)
    print("Environment Name:", settings.env_name)


if __name__ == "__main__":
    main()
