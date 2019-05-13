import requests

if __name__ == '__main__':
    data = """
    curl -i -X POST https://identity.tyo2.conoha.io/v2.0/tokens \
     -H "Accept: application/json" \
     -d '{"auth":{"passwordCredentials":{"username":"gncu97565063","password":"DaSdLsDsAl1!"},"tenantId":"b69db4045b7543868be39756c55743a3"}}'
    """

    json_str = '{"auth":{"passwordCredentials":{"username":"gncu97565063","password":"DaSdLsDsAl1!"},"tenantId":"b69db4045b7543868be39756c55743a3"}}'
    kn_url = 'https://identity.tyo2.conoha.io/v2.0/tokens'
    headers = "Accept: application/json"

    r = requests.post(kn_url, data=json_str)
    print(r.text)

