from genaikeys import SecretKeeper


def main():
    sck = SecretKeeper.gcp()
    # This assumes that you already have a secret called "my-secret" in your secret manager
    # We do not support writing secrets to the secret manager, only reading
    print("[GCP] my-secret: ", sck.get_secret("my-secret"))


if __name__ == "__main__":
    main()
