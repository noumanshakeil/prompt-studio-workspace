import pytest

@pytest.mark.asyncio
async def test_prompt_preview(client):
    p = await client.post("/api/projects", json={"name": "welcome"})
    pid = p.json()["id"]
    v = await client.post(
        f"/api/projects/{pid}/versions",
        json={"template": "Write a greeting for {{ name }}", "variables": {"name": "Ada"}},
    )
    vid = v.json()["id"]
    prev = await client.post(f"/api/versions/{vid}/preview", json={"variables": {"name": "Ada"}})
    assert prev.status_code == 200
    assert "Ada" in prev.json()["rendered"]
    assert prev.json()["output"]
