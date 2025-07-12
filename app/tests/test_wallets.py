def test_create_wallets(client):
    response = client.post("/wallets/", params={"qtd": 2})
    assert response.status_code == 200
    assert "addresses" in response.json()
    assert len(response.json()["addresses"]) == 2

def test_list_wallets(client):
    response = client.get("/wallets/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
