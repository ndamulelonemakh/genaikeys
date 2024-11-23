from genaikeys import SecretKeeper


def main():
    sck = SecretKeeper.from_defaults()
    # This assumes that you already have a secret called "my-secret" in your secret manager
    # We do not support writing secrets to the secret manager, only reading
    print("[AZURE] my-secret: ", sck.get_secret("my-secret"))


if __name__ == "__main__":
    main()
