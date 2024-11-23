from genaikeys import SecretKeeper


def main():
    sck = SecretKeeper.aws(region_name='us-west-2')
    # This assumes that you already have a secret called "my-secret" in your secret manager
    # We do not support writing secrets to the secret manager, only reading
    print("[AWS] my-secret: ", sck.get_secret("my-secret"))


if __name__ == "__main__":
    main()
