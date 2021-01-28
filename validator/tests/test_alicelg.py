import pytest
from aioresponses import aioresponses

from ..alicelg import get_routes, query_rpki_invalid_community
from ..status import RouteEntry


@pytest.mark.asyncio
async def test_query_rpki_invalid_community():
    payload = {
        'rpki': {
            'invalid': ['1', '2', '3'],
        },
    }
    with aioresponses() as http_mock:
        http_mock.get('http://example.net/api/v1/config', status=200, payload=payload)
        response = await query_rpki_invalid_community('http://example.net/api/v1')
    assert response == '1:2:3'

    payload = {
        'rpki': {
            'invalid': [],
        },
    }
    with aioresponses() as http_mock:
        http_mock.get('http://example.net/api/v1/config', status=200, payload=payload)
        response = await query_rpki_invalid_community('http://example.net/api/v1')
    assert response is None

    payload = {}
    with aioresponses() as http_mock:
        http_mock.get('http://example.net/api/v1/config', status=200, payload=payload)
        response = await query_rpki_invalid_community('http://example.net/api/v1')
    assert response is None


@pytest.mark.asyncio
async def test_get_routes():
    payload_routeservers = {
        "routeservers": [
            {"id": "server1", "group": "group1"},
            {"id": "server2", "group": "group1"},
            {"id": "server-ignored", "group": "group2"},
        ],
    }
    payload_neighbors = {
        "neighbours": [
            {"id": "peer1", "state": "up", "address": "192.0.2.1", "asn": 64501},
            {"id": "peer-ignored", "state": "down"},
        ],
    }
    payload_routes = {
        "imported": [
            {"network": "192.0.2.0/24", "bgp": {"as_path": [64501, 64502], "communities": [[64501, 1], [64501, 2]], "large_communities": [[64501, 10, 20]]}}
        ],
    }
    with aioresponses() as http_mock:
        http_mock.get('http://example.net/api/v1/routeservers', status=200, payload=payload_routeservers)
        http_mock.get('http://example.net/api/v1/routeservers/server1/neighbors', status=200, payload=payload_neighbors)
        http_mock.get('http://example.net/api/v1/routeservers/server2/neighbors', status=200, payload=payload_neighbors)
        http_mock.get('http://example.net/api/v1/routeservers/server1/neighbors/peer1/routes', status=200, payload=payload_routes)
        http_mock.get('http://example.net/api/v1/routeservers/server2/neighbors/peer1/routes', status=200, payload=payload_routes)
        response = [r async for r in get_routes('http://example.net/api/v1', 'group1')]
    print(response)
    assert response == [
        RouteEntry(origin=64502, aspath='64501 64502', prefix='192.0.2.0/24', peer_ip='192.0.2.1', peer_as=64501, communities={'64501:2', '64501:10:20', '64501:1'}, source='Alice route server server1'), RouteEntry(origin=64502, aspath='64501 64502', prefix='192.0.2.0/24', peer_ip='192.0.2.1', peer_as=64501, communities={'64501:2', '64501:10:20', '64501:1'}, source='Alice route server server2')]